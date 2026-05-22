"""FastAPI dependencies: API key auth + rate limiting + JWT auth."""
from __future__ import annotations

from datetime import date, datetime

from fastapi import Depends, Header, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import decode_access_token, hash_api_key
from app.db.session import get_db
from app.models import AdminUser, APIKey, APIKeyUsage, Customer, Subscription


# Tier -> daily limit. None means unlimited.
_TIER_LIMITS: dict[str, int | None] = {
    "free": settings.RATE_LIMIT_FREE_PER_DAY,
    "starter": settings.RATE_LIMIT_STARTER_PER_DAY,
    "pro": settings.RATE_LIMIT_PRO_PER_DAY,
    "enterprise": None,
}


bearer_scheme = HTTPBearer(auto_error=False)


def _extract_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    api_key_qs: str | None = Query(default=None, alias="api_key"),
) -> str | None:
    return x_api_key or api_key_qs


def _resolve_daily_limit(api_key: APIKey) -> int | None:
    """Per-key override beats tier default. 0 means unlimited."""
    if api_key.daily_limit_override is not None:
        return None if api_key.daily_limit_override == 0 else api_key.daily_limit_override
    return _TIER_LIMITS.get(api_key.tier, settings.RATE_LIMIT_FREE_PER_DAY)


def require_api_key(
    db: Session = Depends(get_db),
    presented: str | None = Depends(_extract_api_key),
) -> APIKey:
    """Validate API key, enforce rate limit, increment usage."""
    if not presented:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Pass via 'X-API-Key' header or 'api_key' query param.",
        )

    key_hash = hash_api_key(presented)
    api_key = db.scalar(select(APIKey).where(APIKey.key_hash == key_hash))

    if not api_key or not api_key.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
        )

    # Verify customer is active
    customer = db.get(Customer, api_key.customer_id)
    if not customer or not customer.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is inactive.",
        )

    # Rate limit check
    limit = _resolve_daily_limit(api_key)
    today = date.today()

    usage = db.scalar(
        select(APIKeyUsage).where(
            APIKeyUsage.api_key_id == api_key.id,
            APIKeyUsage.usage_date == today,
        )
    )

    if usage is None:
        usage = APIKeyUsage(api_key_id=api_key.id, usage_date=today, request_count=0)
        db.add(usage)
        db.flush()

    if limit is not None and usage.request_count >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily rate limit of {limit} requests exceeded for tier '{api_key.tier}'. "
                "Resets at 00:00 UTC. Upgrade your plan at /pricing."
            ),
            headers={"Retry-After": "3600"},
        )

    usage.request_count += 1
    api_key.last_used_at = datetime.utcnow()
    db.commit()

    return api_key


def require_admin(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> AdminUser:
    """Validate admin JWT."""
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(creds.credentials)
    if not payload or payload.get("type") != "admin":
        raise HTTPException(status_code=401, detail="Invalid or expired admin token.")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Malformed token.")

    user = db.scalar(select(AdminUser).where(AdminUser.email == email))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="Admin not found or inactive.")

    return user


def require_customer(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Customer:
    """Validate customer JWT (used by dashboard endpoints)."""
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Customer bearer token required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(creds.credentials)
    if not payload or payload.get("type") != "customer":
        raise HTTPException(status_code=401, detail="Invalid or expired customer token.")

    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=401, detail="Malformed token.")

    customer = db.scalar(select(Customer).where(Customer.email == email))
    if not customer or not customer.is_active:
        raise HTTPException(status_code=401, detail="Customer not found or inactive.")

    return customer
