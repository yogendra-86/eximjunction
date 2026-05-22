"""Billing endpoints: plans, checkout, payment verification, webhook."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.dependencies import require_customer
from app.db.session import get_db
from app.models import APIKey, Customer, Payment, Plan, Subscription
from app.schemas.billing import (
    CheckoutRequest,
    CheckoutResponse,
    PaymentOut,
    PaymentVerifyRequest,
    PlanOut,
    SubscriptionOut,
)
from app.services.razorpay_client import razorpay_client

log = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])


def _format_price(price_paise: int) -> str:
    """Convert paise to display string like '₹999/month' or 'Free'."""
    if price_paise == 0:
        return "Free"
    return f"₹{price_paise // 100:,}"


def _plan_to_out(plan: Plan) -> PlanOut:
    """Build PlanOut from Plan, including display price."""
    features = []
    if plan.features:
        try:
            features = json.loads(plan.features)
        except (json.JSONDecodeError, TypeError):
            features = []

    period_suffix = "/month" if plan.billing_period == "monthly" else "/year"
    if plan.price_inr == 0:
        display = "Free"
    else:
        display = f"{_format_price(plan.price_inr)}{period_suffix}"

    return PlanOut(
        id=plan.id,
        code=plan.code,
        name=plan.name,
        tier=plan.tier,
        price_inr=plan.price_inr,
        price_display=display,
        billing_period=plan.billing_period,
        daily_request_limit=plan.daily_request_limit,
        features=features,
        is_active=plan.is_active,
        sort_order=plan.sort_order,
    )


# ========== Plans (public) ==========

@router.get("/plans", response_model=list[PlanOut], summary="List all active subscription plans")
def list_plans(db: Session = Depends(get_db)):
    plans = db.scalars(
        select(Plan).where(Plan.is_active.is_(True)).order_by(Plan.sort_order, Plan.price_inr)
    ).all()
    return [_plan_to_out(p) for p in plans]


# ========== Customer subscription ==========

@router.get("/subscription", response_model=SubscriptionOut | None, summary="Current subscription")
def my_subscription(
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    sub = db.scalar(
        select(Subscription)
        .where(Subscription.customer_id == customer.id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
    )
    if not sub:
        return None

    plan = db.get(Plan, sub.plan_id)
    return SubscriptionOut(
        id=sub.id,
        status=sub.status,
        plan=_plan_to_out(plan),
        started_at=sub.started_at,
        current_period_end=sub.current_period_end,
        cancelled_at=sub.cancelled_at,
        created_at=sub.created_at,
    )


# ========== Checkout flow ==========

@router.post(
    "/checkout",
    response_model=CheckoutResponse,
    summary="Initiate Razorpay checkout for a paid plan",
)
def checkout(
    payload: CheckoutRequest,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    plan = db.scalar(select(Plan).where(Plan.code == payload.plan_code, Plan.is_active.is_(True)))
    if not plan:
        raise HTTPException(status_code=404, detail=f"Plan '{payload.plan_code}' not found.")

    if plan.price_inr == 0:
        raise HTTPException(status_code=400, detail="Free plan does not require checkout.")

    # Create a pending Subscription
    sub = Subscription(
        customer_id=customer.id,
        plan_id=plan.id,
        status="pending",
    )
    db.add(sub)
    db.flush()

    # Create Razorpay order
    receipt = f"sub_{sub.id}_{customer.id}"
    order = razorpay_client.create_order(
        amount_paise=plan.price_inr,
        currency="INR",
        receipt=receipt,
    )

    # Record the pending payment
    payment = Payment(
        subscription_id=sub.id,
        customer_id=customer.id,
        razorpay_order_id=order["id"],
        amount_paise=plan.price_inr,
        currency="INR",
        status="created",
    )
    db.add(payment)
    db.commit()

    return CheckoutResponse(
        razorpay_order_id=order["id"],
        razorpay_key_id=settings.RAZORPAY_KEY_ID or "rzp_test_MOCK",
        amount_paise=plan.price_inr,
        currency="INR",
        subscription_id=sub.id,
        plan_name=plan.name,
        customer_email=customer.email,
        customer_name=customer.full_name,
        customer_phone=customer.phone,
        mock_mode=razorpay_client.is_mock,
    )


@router.post(
    "/verify-payment",
    response_model=SubscriptionOut,
    summary="Verify Razorpay payment and activate subscription",
)
def verify_payment(
    payload: PaymentVerifyRequest,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    # Find the payment
    payment = db.scalar(
        select(Payment).where(Payment.razorpay_order_id == payload.razorpay_order_id)
    )
    if not payment or payment.customer_id != customer.id:
        raise HTTPException(status_code=404, detail="Order not found.")

    # Verify signature
    if not razorpay_client.verify_payment_signature(
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    ):
        payment.status = "failed"
        payment.error_description = "Signature verification failed"
        db.commit()
        raise HTTPException(status_code=400, detail="Payment signature verification failed.")

    # Mark payment captured
    payment.razorpay_payment_id = payload.razorpay_payment_id
    payment.razorpay_signature = payload.razorpay_signature
    payment.status = "captured"
    payment.captured_at = datetime.utcnow()

    # Activate the subscription
    sub = db.get(Subscription, payment.subscription_id)
    if not sub:
        raise HTTPException(status_code=500, detail="Subscription missing for payment.")

    plan = db.get(Plan, sub.plan_id)
    period_days = 365 if plan.billing_period == "annual" else 30

    # Cancel any previous active subscriptions
    prev = db.scalars(
        select(Subscription).where(
            Subscription.customer_id == customer.id,
            Subscription.status == "active",
            Subscription.id != sub.id,
        )
    ).all()
    for p in prev:
        p.status = "cancelled"
        p.cancelled_at = datetime.utcnow()

    sub.status = "active"
    sub.started_at = datetime.utcnow()
    sub.current_period_end = datetime.utcnow() + timedelta(days=period_days)

    # Upgrade all the customer's API keys to the new tier
    keys = db.scalars(select(APIKey).where(APIKey.customer_id == customer.id, APIKey.is_active.is_(True))).all()
    for k in keys:
        k.tier = plan.tier

    db.commit()

    return SubscriptionOut(
        id=sub.id,
        status=sub.status,
        plan=_plan_to_out(plan),
        started_at=sub.started_at,
        current_period_end=sub.current_period_end,
        cancelled_at=sub.cancelled_at,
        created_at=sub.created_at,
    )


@router.post(
    "/mock-success/{order_id}",
    response_model=SubscriptionOut,
    summary="DEV ONLY: simulate a successful payment without Razorpay",
)
def mock_payment_success(
    order_id: str,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    """Shortcut for local dev when no Razorpay keys are configured."""
    if not razorpay_client.is_mock:
        raise HTTPException(status_code=400, detail="Mock endpoint only available when Razorpay is not configured.")

    # Reuse verify_payment logic with synthetic signature
    return verify_payment(
        PaymentVerifyRequest(
            razorpay_order_id=order_id,
            razorpay_payment_id=f"pay_mock_{order_id[-8:]}",
            razorpay_signature="mock_signature_xyz",
        ),
        customer=customer,
        db=db,
    )


# ========== Webhooks (Razorpay -> server) ==========

@router.post("/webhook", summary="Razorpay webhook for async events")
async def razorpay_webhook(
    request: Request,
    x_razorpay_signature: str | None = Header(default=None, alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
):
    """Handle Razorpay webhook events (payment.captured, payment.failed)."""
    body = await request.body()

    if not x_razorpay_signature or not razorpay_client.verify_webhook_signature(body, x_razorpay_signature):
        raise HTTPException(status_code=400, detail="Invalid webhook signature.")

    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON.")

    event_type = event.get("event")
    payload = event.get("payload", {})
    log.info("Razorpay webhook received: %s", event_type)

    # Idempotent: only process if we have matching order
    if event_type in ("payment.captured", "payment.failed"):
        entity = payload.get("payment", {}).get("entity", {})
        order_id = entity.get("order_id")
        payment_id = entity.get("id")

        if not order_id:
            return {"ok": True}

        payment = db.scalar(select(Payment).where(Payment.razorpay_order_id == order_id))
        if not payment:
            log.warning("Webhook for unknown order: %s", order_id)
            return {"ok": True}

        if event_type == "payment.captured" and payment.status != "captured":
            payment.razorpay_payment_id = payment_id
            payment.status = "captured"
            payment.captured_at = datetime.utcnow()
            # Activate subscription
            sub = db.get(Subscription, payment.subscription_id)
            if sub and sub.status != "active":
                plan = db.get(Plan, sub.plan_id)
                period_days = 365 if plan.billing_period == "annual" else 30
                sub.status = "active"
                sub.started_at = datetime.utcnow()
                sub.current_period_end = datetime.utcnow() + timedelta(days=period_days)
                # Upgrade customer's keys
                keys = db.scalars(
                    select(APIKey).where(APIKey.customer_id == payment.customer_id, APIKey.is_active.is_(True))
                ).all()
                for k in keys:
                    k.tier = plan.tier
            db.commit()

        elif event_type == "payment.failed":
            payment.status = "failed"
            payment.error_code = entity.get("error_code")
            payment.error_description = entity.get("error_description")
            db.commit()

    return {"ok": True}


# ========== Payment history ==========

@router.get("/payments", response_model=list[PaymentOut], summary="Your payment history")
def my_payments(
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    return db.scalars(
        select(Payment).where(Payment.customer_id == customer.id).order_by(Payment.created_at.desc())
    ).all()
