"""Pydantic schemas for billing endpoints."""
from __future__ import annotations

import json
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    code: str
    name: str
    tier: str
    price_inr: int  # in paise
    price_display: str = ""  # e.g. "₹999/month"
    billing_period: str
    daily_request_limit: int | None
    features: list[str] = []
    is_active: bool
    sort_order: int

    @field_validator("features", mode="before")
    @classmethod
    def parse_features(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except (json.JSONDecodeError, TypeError):
                return []
        return v or []


class SubscriptionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    plan: PlanOut
    started_at: datetime | None
    current_period_end: datetime | None
    cancelled_at: datetime | None
    created_at: datetime


class CheckoutRequest(BaseModel):
    plan_code: str = Field(..., description="Plan code, e.g. 'starter', 'pro'")


class CheckoutResponse(BaseModel):
    """What the frontend needs to launch Razorpay checkout."""
    razorpay_order_id: str
    razorpay_key_id: str
    amount_paise: int
    currency: str
    subscription_id: int
    plan_name: str
    customer_email: str
    customer_name: str | None = None
    customer_phone: str | None = None
    mock_mode: bool = False
    # If mock_mode=True, the frontend should call /billing/mock-success to fake a payment


class PaymentVerifyRequest(BaseModel):
    """Sent by frontend after successful Razorpay checkout."""
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class PaymentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    razorpay_order_id: str | None
    razorpay_payment_id: str | None
    amount_paise: int
    currency: str
    status: str
    created_at: datetime
    captured_at: datetime | None
