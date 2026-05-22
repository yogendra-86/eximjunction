"""Billing models: plans, subscriptions, payments."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Plan(Base):
    """Subscription plan/tier definition. Seeded from plans.json."""
    __tablename__ = "plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)  # 'free', 'starter', etc.
    name: Mapped[str] = mapped_column(String(120))
    tier: Mapped[str] = mapped_column(String(20))  # maps to APIKey.tier
    price_inr: Mapped[int] = mapped_column(Integer, default=0)  # in paise (₹999 = 99900)
    billing_period: Mapped[str] = mapped_column(String(20), default="monthly")  # monthly|annual
    daily_request_limit: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = unlimited
    features: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list of feature strings
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class Subscription(Base):
    """A customer's active or past subscription to a plan."""
    __tablename__ = "subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("plans.id"))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    # status: pending | active | past_due | cancelled | expired
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    customer = relationship("Customer", back_populates="subscriptions")
    plan = relationship("Plan")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """A Razorpay payment record."""
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subscription_id: Mapped[int | None] = mapped_column(ForeignKey("subscriptions.id"), nullable=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)

    # Razorpay identifiers
    razorpay_order_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(80), index=True, nullable=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)

    amount_paise: Mapped[int] = mapped_column(Integer)  # amount in paise (₹999 = 99900)
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    status: Mapped[str] = mapped_column(String(20), default="created")
    # status: created | authorized | captured | failed | refunded
    error_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    error_description: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    subscription = relationship("Subscription", back_populates="payments")
    customer = relationship("Customer")
