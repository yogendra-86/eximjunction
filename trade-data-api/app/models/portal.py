"""Portal-specific ORM models.

These are ADDITIVE — existing tables (trade_flows, tariffs, etc.) are untouched.
All portal models live here and are imported alongside existing models.
"""
from __future__ import annotations
from datetime import datetime, date
from sqlalchemy import (
    BigInteger, Boolean, DateTime, Date, ForeignKey,
    Integer, String, Text, JSON, UniqueConstraint
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base

BigIntPK = BigInteger().with_variant(Integer(), "sqlite")


class PortalPlan(Base):
    """Portal-specific subscription plans (separate from API plans)."""
    __tablename__ = "portal_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    price_inr: Mapped[int] = mapped_column(Integer, default=0)        # paise
    billing_period: Mapped[str] = mapped_column(String(20), default="monthly")
    records_per_search: Mapped[int | None] = mapped_column(Integer, nullable=True)  # None = unlimited
    can_export_csv: Mapped[bool] = mapped_column(Boolean, default=False)
    can_export_excel: Mapped[bool] = mapped_column(Boolean, default=False)
    can_use_api: Mapped[bool] = mapped_column(Boolean, default=False)
    features: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON list
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)


class PortalSubscription(Base):
    """A customer's portal plan subscription."""
    __tablename__ = "portal_subscriptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    plan_id: Mapped[int] = mapped_column(ForeignKey("portal_plans.id"))
    status: Mapped[str] = mapped_column(String(20), default="active")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    current_period_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    plan = relationship("PortalPlan")


class PortalSearch(Base):
    """Audit log of every portal search — used for analytics and rate limiting."""
    __tablename__ = "portal_searches"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    hs_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    reporter: Mapped[str | None] = mapped_column(String(3), nullable=True)
    partner: Mapped[str | None] = mapped_column(String(3), nullable=True)
    flow_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    year_from: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year_to: Mapped[int | None] = mapped_column(Integer, nullable=True)
    records_returned: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class PortalExport(Base):
    """Record of every CSV/Excel export download."""
    __tablename__ = "portal_exports"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    search_params: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON of search params
    file_format: Mapped[str] = mapped_column(String(10), default="csv")
    records_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class EximServiceRequest(Base):
    """IEC / RCMC / AD Code registration service requests."""
    __tablename__ = "exim_service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)
    service_type: Mapped[str] = mapped_column(String(40))
    # service_type: iec | rcmc | ad_code | bundle | fssai | retainer
    status: Mapped[str] = mapped_column(String(20), default="submitted")
    # status: submitted | documents_received | in_progress | completed | rejected
    applicant_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    company_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    pan_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(160), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    fee_paise: Mapped[int] = mapped_column(Integer, default=0)
    payment_status: Mapped[str] = mapped_column(String(20), default="pending")
    razorpay_order_id: Mapped[str | None] = mapped_column(String(80), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class DataIngestionLog(Base):
    """Tracks every Comtrade data fetch to avoid duplicates and monitor freshness."""
    __tablename__ = "data_ingestion_log"

    id: Mapped[int] = mapped_column(BigIntPK, primary_key=True, autoincrement=True)
    hs_code: Mapped[str] = mapped_column(String(10), index=True)
    reporter_m49: Mapped[int | None] = mapped_column(Integer, nullable=True)
    partner_m49: Mapped[int | None] = mapped_column(Integer, nullable=True)
    year: Mapped[int] = mapped_column(Integer)
    flow_type: Mapped[str] = mapped_column(String(10))
    records_fetched: Mapped[int] = mapped_column(Integer, default=0)
    records_inserted: Mapped[int] = mapped_column(Integer, default=0)
    source: Mapped[str] = mapped_column(String(40), default="comtrade")
    status: Mapped[str] = mapped_column(String(20), default="success")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        UniqueConstraint("hs_code", "reporter_m49", "partner_m49", "year", "flow_type",
                         name="uq_ingestion_log"),
    )
