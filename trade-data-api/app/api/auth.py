"""Auth endpoints: customer signup/login, admin login, API key management."""
from __future__ import annotations

from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import (
    _resolve_daily_limit,
    require_admin,
    require_customer,
)
from app.core.security import (
    create_access_token,
    generate_api_key,
    hash_password,
    verify_password,
)
from app.db.session import get_db
from app.models import (
    AdminUser,
    APIKey,
    APIKeyUsage,
    Customer,
    Plan,
    Subscription,
)
from app.schemas.auth import (
    AdminUserOut,
    APIKeyCreate,
    APIKeyCreated,
    APIKeyOut,
    APIKeyUsageReport,
    APIKeyUsageStat,
    CustomerOut,
    CustomerSignup,
    LoginRequest,
    TokenResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ========== Customer signup & login ==========

@router.post("/signup", response_model=TokenResponse, status_code=201, summary="Sign up as a customer")
def signup(payload: CustomerSignup, db: Session = Depends(get_db)):
    existing = db.scalar(select(Customer).where(Customer.email == payload.email))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered.")

    customer = Customer(
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
        company_name=payload.company_name,
        phone=payload.phone,
        is_active=True,
        email_verified=False,
    )
    db.add(customer)
    db.flush()

    # Auto-create a Free subscription
    free_plan = db.scalar(select(Plan).where(Plan.code == "free"))
    if free_plan:
        sub = Subscription(
            customer_id=customer.id,
            plan_id=free_plan.id,
            status="active",
            started_at=datetime.utcnow(),
            current_period_end=datetime.utcnow() + timedelta(days=36500),  # ~100 years (free forever)
        )
        db.add(sub)
        db.flush()

        # Auto-create a default API key on the free tier
        plaintext, prefix, key_hash = generate_api_key()
        api_key = APIKey(
            customer_id=customer.id,
            key_prefix=prefix,
            key_hash=key_hash,
            name="Default key",
            tier="free",
            is_active=True,
        )
        db.add(api_key)

    db.commit()

    token = create_access_token(subject=customer.email, token_type="customer")
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


@router.post("/login", response_model=TokenResponse, summary="Customer login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    customer = db.scalar(select(Customer).where(Customer.email == payload.email))
    if not customer or not customer.is_active or not verify_password(payload.password, customer.password_hash):
        # Run verify even when customer is None to avoid timing attacks
        if customer is None:
            verify_password(payload.password, "$2b$12$invalidinvalidinvalidinvalidinvalidinvalidinvalidinvalidinvali")
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(subject=customer.email, token_type="customer")
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


@router.get("/me", response_model=CustomerOut, summary="Get current customer")
def me(customer: Customer = Depends(require_customer)):
    return customer


# ========== Admin login ==========

@router.post("/admin/login", response_model=TokenResponse, summary="Admin login")
def admin_login(payload: LoginRequest, db: Session = Depends(get_db)):
    admin = db.scalar(select(AdminUser).where(AdminUser.email == payload.email))
    if not admin or not admin.is_active or not verify_password(payload.password, admin.password_hash):
        if admin is None:
            verify_password(payload.password, "$2b$12$invalidinvalidinvalidinvalidinvalidinvalidinvalidinvalidinvali")
        raise HTTPException(status_code=401, detail="Invalid credentials.")

    token = create_access_token(subject=admin.email, token_type="admin")
    return TokenResponse(access_token=token, expires_in_minutes=settings.JWT_EXPIRE_MINUTES)


@router.get("/admin/me", response_model=AdminUserOut, summary="Get current admin")
def admin_me(admin: AdminUser = Depends(require_admin)):
    return admin


# ========== API key management (customer-owned) ==========

@router.post(
    "/keys",
    response_model=APIKeyCreated,
    status_code=201,
    summary="Create an API key (customer)",
)
def create_key(
    payload: APIKeyCreate,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    # Determine tier from active subscription
    sub = db.scalar(
        select(Subscription)
        .where(Subscription.customer_id == customer.id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
    )
    tier = "free"
    if sub:
        plan = db.get(Plan, sub.plan_id)
        if plan:
            tier = plan.tier

    plaintext, prefix, key_hash = generate_api_key()
    api_key = APIKey(
        customer_id=customer.id,
        key_prefix=prefix,
        key_hash=key_hash,
        name=payload.name,
        tier=tier,
        is_active=True,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)

    return APIKeyCreated(
        id=api_key.id,
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        tier=api_key.tier,
        daily_limit_override=api_key.daily_limit_override,
        is_active=api_key.is_active,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        plaintext_key=plaintext,
    )


@router.get("/keys", response_model=list[APIKeyOut], summary="List your API keys")
def list_keys(
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(APIKey)
        .where(APIKey.customer_id == customer.id)
        .order_by(APIKey.created_at.desc())
    ).all()


@router.delete("/keys/{key_id}", status_code=204, summary="Revoke an API key")
def revoke_key(
    key_id: int,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    api_key = db.get(APIKey, key_id)
    if not api_key or api_key.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="API key not found.")
    api_key.is_active = False
    db.commit()


@router.get(
    "/keys/{key_id}/usage",
    response_model=APIKeyUsageReport,
    summary="Usage report for the last 30 days",
)
def key_usage(
    key_id: int,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    api_key = db.get(APIKey, key_id)
    if not api_key or api_key.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="API key not found.")

    cutoff = date.today() - timedelta(days=30)
    rows = db.scalars(
        select(APIKeyUsage)
        .where(APIKeyUsage.api_key_id == key_id, APIKeyUsage.usage_date >= cutoff)
        .order_by(APIKeyUsage.usage_date)
    ).all()

    daily = [
        APIKeyUsageStat(usage_date=r.usage_date.isoformat(), request_count=r.request_count)
        for r in rows
    ]

    return APIKeyUsageReport(
        key_prefix=api_key.key_prefix,
        name=api_key.name,
        tier=api_key.tier,
        daily_limit=_resolve_daily_limit(api_key),
        total_requests_30d=sum(r.request_count for r in rows),
        daily=daily,
    )
