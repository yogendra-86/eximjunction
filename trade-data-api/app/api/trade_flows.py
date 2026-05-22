"""Trade flow trends endpoint."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_api_key
from app.db.session import get_db
from app.models import Country, HSCode, TradeFlow
from app.schemas.trade import (
    CountryOut,
    TradeTrendPoint,
    TradeTrendResponse,
)

router = APIRouter(
    prefix="/trade-flows",
    tags=["trade-flows"],
    dependencies=[Depends(require_api_key)],
)


def _compute_cagr(points: list[TradeTrendPoint]) -> float | None:
    if len(points) < 2:
        return None
    first, last = points[0], points[-1]
    if first.value_usd <= 0 or last.value_usd <= 0:
        return None
    n = last.year - first.year
    if n <= 0:
        return None
    cagr = (last.value_usd / first.value_usd) ** (1 / n) - 1
    return round(cagr * 100, 2)


@router.get(
    "",
    response_model=TradeTrendResponse,
    summary="Trade flow trend between two countries for a product",
)
def trade_flow_trend(
    reporter: str = Query(..., description="ISO alpha-2 of reporter"),
    partner: str = Query(..., description="ISO alpha-2 of partner"),
    hs_code: str = Query(..., description="HS code (any level)"),
    flow: str = Query("export", pattern="^(import|export)$"),
    year_from: int = Query(2019, ge=1990),
    year_to: int = Query(2024, le=2030),
    db: Session = Depends(get_db),
):
    if year_from > year_to:
        raise HTTPException(status_code=400, detail="year_from must be <= year_to")

    rep = db.scalar(select(Country).where(Country.iso_alpha2 == reporter.upper()))
    if not rep:
        raise HTTPException(status_code=404, detail=f"Reporter '{reporter}' not found")
    par = db.scalar(select(Country).where(Country.iso_alpha2 == partner.upper()))
    if not par:
        raise HTTPException(status_code=404, detail=f"Partner '{partner}' not found")
    hs = db.scalar(select(HSCode).where(HSCode.code == hs_code))
    if not hs:
        raise HTTPException(status_code=404, detail=f"HS code '{hs_code}' not found")

    flows = db.scalars(
        select(TradeFlow)
        .where(
            TradeFlow.reporter_id == rep.id,
            TradeFlow.partner_id == par.id,
            TradeFlow.hs_code == hs_code,
            TradeFlow.flow_type == flow,
            TradeFlow.year >= year_from,
            TradeFlow.year <= year_to,
        )
        .order_by(TradeFlow.year)
    ).all()

    points = [
        TradeTrendPoint(year=f.year, value_usd=f.value_usd, quantity=f.quantity)
        for f in flows
    ]
    total = sum(p.value_usd for p in points)

    return TradeTrendResponse(
        reporter=CountryOut.model_validate(rep),
        partner=CountryOut.model_validate(par),
        hs_code=hs_code,
        hs_description=hs.description,
        flow_type=flow,
        points=points,
        total_value_usd=total,
        growth_rate_pct=_compute_cagr(points),
    )
