"""Portal API endpoints — data search, export, services.

All endpoints check portal subscription tier before returning data.
Row limits enforced server-side based on plan.
"""
from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_customer
from app.db.session import get_db
from app.models import Country, HSCode, TradeFlow, Tariff, ComplianceDoc
from app.models.auth import Customer
from app.models.portal import (
    DataIngestionLog, EximServiceRequest,
    PortalExport, PortalPlan, PortalSearch, PortalSubscription,
)

router = APIRouter(prefix="/portal", tags=["portal"])

# ── Tier enforcement ─────────────────────────────────────────────────────────

SERVICE_FEES = {
    "iec":      299900,   # ₹2,999
    "rcmc":     399900,   # ₹3,999
    "ad_code":  199900,   # ₹1,999
    "bundle":   999900,   # ₹9,999
    "retainer": 499900,   # ₹4,999/month
}


def _get_portal_plan(customer: Customer, db: Session) -> PortalPlan | None:
    """Get customer's active portal subscription plan. None = free tier."""
    sub = db.scalar(
        select(PortalSubscription)
        .where(
            PortalSubscription.customer_id == customer.id,
            PortalSubscription.status == "active",
        )
        .order_by(PortalSubscription.created_at.desc())
    )
    if not sub:
        return None
    return db.get(PortalPlan, sub.plan_id)


def _record_limit(plan: PortalPlan | None) -> int:
    """How many rows can this customer see per search?"""
    if plan is None:
        return 10           # Free tier
    if plan.records_per_search is None:
        return 99999        # Unlimited
    return plan.records_per_search


# ── Public endpoints (no auth) ────────────────────────────────────────────────

@router.get("/plans", summary="List portal subscription plans")
def list_portal_plans(db: Session = Depends(get_db)):
    plans = db.scalars(
        select(PortalPlan).where(PortalPlan.is_active.is_(True)).order_by(PortalPlan.sort_order)
    ).all()
    return [
        {
            "id": p.id,
            "code": p.code,
            "name": p.name,
            "price_inr": p.price_inr,
            "price_display": f"₹{p.price_inr // 100:,}/month" if p.price_inr > 0 else "Free",
            "billing_period": p.billing_period,
            "records_per_search": p.records_per_search,
            "can_export_csv": p.can_export_csv,
            "can_export_excel": p.can_export_excel,
            "can_use_api": p.can_use_api,
            "features": json.loads(p.features) if p.features else [],
        }
        for p in plans
    ]


# ── Search (authenticated) ────────────────────────────────────────────────────

@router.get("/search", summary="Search trade data with filters")
def search(
    q: str | None = Query(None, description="Keyword or HS code"),
    hs_code: str | None = Query(None, description="Specific HS code"),
    reporter: str | None = Query(None, description="Exporter ISO alpha-2"),
    partner: str | None = Query(None, description="Importer ISO alpha-2"),
    flow: str = Query("export", pattern="^(import|export)$"),
    year_from: int = Query(2019, ge=1990),
    year_to: int = Query(2024, le=2030),
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    plan  = _get_portal_plan(customer, db)
    limit = _record_limit(plan)

    # Build base query
    query = (
        select(
            TradeFlow.hs_code,
            TradeFlow.year,
            TradeFlow.flow_type,
            TradeFlow.value_usd,
            TradeFlow.quantity,
            TradeFlow.quantity_unit,
            Country.iso_alpha2.label("reporter_iso"),
            Country.name.label("reporter_name"),
        )
        .join(Country, Country.id == TradeFlow.reporter_id)
        .where(
            TradeFlow.flow_type == flow,
            TradeFlow.year >= year_from,
            TradeFlow.year <= year_to,
        )
    )

    # HS code filter
    if hs_code:
        query = query.where(TradeFlow.hs_code == hs_code)
    elif q and q.isdigit():
        # Prefix match for numeric queries
        subq = select(HSCode.code).where(HSCode.code.startswith(q))
        query = query.where(TradeFlow.hs_code.in_(subq))

    # Country filters
    if reporter:
        rep = db.scalar(select(Country).where(Country.iso_alpha2 == reporter.upper()))
        if rep:
            query = query.where(TradeFlow.reporter_id == rep.id)

    if partner:
        par = db.scalar(select(Country).where(Country.iso_alpha2 == partner.upper()))
        if par:
            query = query.where(TradeFlow.partner_id == par.id)

    # Order and limit
    query = query.order_by(TradeFlow.value_usd.desc()).limit(limit + 1)
    rows  = db.execute(query).all()
    has_more = len(rows) > limit
    rows = rows[:limit]

    # Log the search
    db.add(PortalSearch(
        customer_id=customer.id,
        hs_code=hs_code or q,
        reporter=reporter,
        partner=partner,
        flow_type=flow,
        year_from=year_from,
        year_to=year_to,
        records_returned=len(rows),
    ))
    db.commit()

    return {
        "results": [
            {
                "hs_code":       r.hs_code,
                "year":          r.year,
                "flow_type":     r.flow_type,
                "value_usd":     r.value_usd,
                "value_display": f"${r.value_usd / 1e9:.2f}B" if r.value_usd >= 1e9 else f"${r.value_usd / 1e6:.1f}M",
                "quantity":      r.quantity,
                "quantity_unit": r.quantity_unit,
                "reporter_iso":  r.reporter_iso,
                "reporter_name": r.reporter_name,
            }
            for r in rows
        ],
        "count":      len(rows),
        "has_more":   has_more,
        "tier_limit": limit,
        "plan":       plan.name if plan else "Free",
        "can_export": plan.can_export_csv if plan else False,
    }


# ── Export (Starter+) ────────────────────────────────────────────────────────

@router.get("/export", summary="Download search results as CSV or Excel")
def export_data(
    hs_code: str | None = Query(None),
    reporter: str | None = Query(None),
    partner: str | None = Query(None),
    flow: str = Query("export", pattern="^(import|export)$"),
    year_from: int = Query(2019),
    year_to: int = Query(2024),
    format: Literal["csv"] = Query("csv"),
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    plan = _get_portal_plan(customer, db)
    if not plan or not plan.can_export_csv:
        raise HTTPException(
            status_code=403,
            detail="CSV export requires Starter plan or above. Upgrade at /portal/plans.",
        )

    # Fetch all matching rows (no row limit for export)
    query = (
        select(
            TradeFlow.hs_code,
            HSCode.description.label("hs_description"),
            TradeFlow.year,
            TradeFlow.flow_type,
            TradeFlow.value_usd,
            TradeFlow.quantity,
            TradeFlow.quantity_unit,
            Country.iso_alpha2.label("reporter_iso"),
            Country.name.label("reporter_name"),
        )
        .join(Country, Country.id == TradeFlow.reporter_id)
        .outerjoin(HSCode, HSCode.code == TradeFlow.hs_code)
        .where(
            TradeFlow.flow_type == flow,
            TradeFlow.year >= year_from,
            TradeFlow.year <= year_to,
        )
    )

    if hs_code:
        query = query.where(TradeFlow.hs_code == hs_code)
    if reporter:
        rep = db.scalar(select(Country).where(Country.iso_alpha2 == reporter.upper()))
        if rep:
            query = query.where(TradeFlow.reporter_id == rep.id)
    if partner:
        par = db.scalar(select(Country).where(Country.iso_alpha2 == partner.upper()))
        if par:
            query = query.where(TradeFlow.partner_id == par.id)

    query = query.order_by(TradeFlow.year, TradeFlow.value_usd.desc())
    rows  = db.execute(query).all()

    # Build CSV
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "HS Code", "Description", "Year", "Flow Type",
        "Value (USD)", "Quantity", "Unit", "Reporter ISO", "Reporter Country",
    ])
    for r in rows:
        writer.writerow([
            r.hs_code, r.hs_description or "", r.year, r.flow_type,
            f"{r.value_usd:.2f}", r.quantity or "", r.quantity_unit or "",
            r.reporter_iso, r.reporter_name,
        ])

    # Log export
    db.add(PortalExport(
        customer_id=customer.id,
        search_params=json.dumps({
            "hs_code": hs_code, "reporter": reporter, "partner": partner,
            "flow": flow, "year_from": year_from, "year_to": year_to,
        }),
        file_format=format,
        records_count=len(rows),
    ))
    db.commit()

    filename = f"eximjunction_trade_data_{datetime.now().strftime('%Y%m%d_%H%M')}.csv"
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Product summary ───────────────────────────────────────────────────────────

@router.get("/product/{hs_code}/summary", summary="Full trade summary for an HS code")
def product_summary(
    hs_code: str,
    year: int = Query(2024),
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    hs = db.scalar(select(HSCode).where(HSCode.code == hs_code))
    if not hs:
        raise HTTPException(status_code=404, detail=f"HS code '{hs_code}' not found.")

    plan  = _get_portal_plan(customer, db)
    limit = _record_limit(plan)

    # Top exporters
    top_exporters = db.execute(
        select(Country.iso_alpha2, Country.name, func.sum(TradeFlow.value_usd).label("value"))
        .join(TradeFlow, TradeFlow.reporter_id == Country.id)
        .where(TradeFlow.hs_code == hs_code, TradeFlow.year == year, TradeFlow.flow_type == "export")
        .group_by(Country.id)
        .order_by(func.sum(TradeFlow.value_usd).desc())
        .limit(limit)
    ).all()

    # Trade trend (2019–2024 for India)
    trend = db.execute(
        select(TradeFlow.year, func.sum(TradeFlow.value_usd).label("value"))
        .join(Country, TradeFlow.reporter_id == Country.id)
        .where(
            TradeFlow.hs_code == hs_code,
            TradeFlow.flow_type == "export",
            Country.iso_alpha2 == "IN",
        )
        .group_by(TradeFlow.year)
        .order_by(TradeFlow.year)
    ).all()

    # MFN tariff rates
    tariffs = db.execute(
        select(Country.iso_alpha2.label("reporter"), Tariff.ad_valorem_rate, Tariff.rate_type)
        .join(Country, Country.id == Tariff.reporter_id)
        .where(Tariff.hs_code == hs_code, Tariff.rate_type == "MFN", Tariff.year == year)
        .limit(10)
    ).all()

    return {
        "hs_code":      hs_code,
        "description":  hs.description,
        "short_name":   hs.short_name,
        "top_exporters": [
            {"iso": r.iso_alpha2, "name": r.name, "value_usd": r.value, "rank": i + 1}
            for i, r in enumerate(top_exporters)
        ],
        "india_trend": [
            {"year": r.year, "value_usd": r.value}
            for r in trend
        ],
        "tariff_rates": [
            {"reporter": r.reporter, "rate_pct": r.ad_valorem_rate, "type": r.rate_type}
            for r in tariffs
        ],
        "plan": plan.name if plan else "Free",
    }


# ── EXIM Documentation Services ───────────────────────────────────────────────

@router.get("/services/catalogue", summary="List available EXIM documentation services")
def service_catalogue():
    return [
        {"code": "iec",      "name": "IEC Registration",            "price_inr": 299900, "delivery": "3–5 working days",
         "description": "Importer Exporter Code — mandatory for all import/export activities in India"},
        {"code": "rcmc",     "name": "RCMC Registration",           "price_inr": 399900, "delivery": "7–15 working days",
         "description": "Registration Cum Membership Certificate — required to claim export benefits under FTP"},
        {"code": "ad_code",  "name": "AD Code Registration",        "price_inr": 199900, "delivery": "3–5 working days",
         "description": "Authorised Dealer Code — required for direct bank remittances on exports"},
        {"code": "bundle",   "name": "Export Documentation Bundle", "price_inr": 999900, "delivery": "15 working days",
         "description": "IEC + RCMC + AD Code + one consultation call. Best value for new exporters."},
        {"code": "retainer", "name": "Monthly Compliance Retainer", "price_inr": 499900, "delivery": "Ongoing",
         "description": "Ongoing export compliance support — amendments, renewals, document queries"},
    ]


@router.post("/services/request", status_code=201, summary="Submit EXIM service request")
def submit_service_request(
    service_type: str,
    applicant_name: str,
    company_name: str,
    pan_number: str,
    mobile: str,
    notes: str | None = None,
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    if service_type not in SERVICE_FEES:
        raise HTTPException(status_code=400, detail=f"Unknown service type: {service_type}")

    req = EximServiceRequest(
        customer_id=customer.id,
        service_type=service_type,
        status="submitted",
        applicant_name=applicant_name,
        company_name=company_name,
        pan_number=pan_number,
        mobile=mobile,
        email=customer.email,
        notes=notes,
        fee_paise=SERVICE_FEES[service_type],
        payment_status="pending",
    )
    db.add(req)
    db.commit()
    db.refresh(req)

    return {
        "id": req.id,
        "service_type": req.service_type,
        "status": req.status,
        "fee_inr": req.fee_paise / 100,
        "message": "Request submitted. Our team will contact you within 24 hours to collect documents and process payment.",
    }


@router.get("/services/my-requests", summary="List your EXIM service requests")
def my_requests(
    customer: Customer = Depends(require_customer),
    db: Session = Depends(get_db),
):
    reqs = db.scalars(
        select(EximServiceRequest)
        .where(EximServiceRequest.customer_id == customer.id)
        .order_by(EximServiceRequest.submitted_at.desc())
    ).all()
    return [
        {
            "id": r.id,
            "service_type": r.service_type,
            "status": r.status,
            "fee_inr": r.fee_paise / 100,
            "payment_status": r.payment_status,
            "submitted_at": r.submitted_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        }
        for r in reqs
    ]


# ── Data freshness ────────────────────────────────────────────────────────────

@router.get("/data-status", summary="Show data coverage and last update times")
def data_status(db: Session = Depends(get_db)):
    """Public endpoint — shows visitors what data is available."""
    total_flows = db.scalar(select(func.count()).select_from(TradeFlow)) or 0
    total_hs    = db.scalar(select(func.count()).select_from(HSCode)) or 0
    latest_year = db.scalar(select(func.max(TradeFlow.year))) or 0

    comtrade_rows = db.scalar(
        select(func.count()).select_from(TradeFlow).where(TradeFlow.source == "comtrade")
    ) or 0

    last_fetch = db.scalar(
        select(func.max(DataIngestionLog.fetched_at))
    )

    return {
        "total_trade_flow_records": total_flows,
        "comtrade_records":         comtrade_rows,
        "hs_codes_covered":         total_hs,
        "latest_data_year":         latest_year,
        "last_updated":             last_fetch.isoformat() if last_fetch else None,
        "update_frequency":         "Weekly (every Sunday)",
        "data_source":              "UN Comtrade+",
    }
