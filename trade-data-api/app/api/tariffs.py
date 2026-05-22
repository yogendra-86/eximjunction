"""Tariffs endpoint: query duty rates by reporter, partner, HS code."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_api_key
from app.db.session import get_db
from app.models import Country, HSCode, Tariff
from app.schemas.trade import CountryOut, TariffOut

router = APIRouter(
    prefix="/tariffs",
    tags=["tariffs"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "",
    response_model=list[TariffOut],
    summary="Tariff rates applied by a country to a partner for a product",
)
def get_tariffs(
    reporter: str = Query(..., description="ISO alpha-2 of importing country"),
    hs_code: str = Query(..., description="HS code"),
    partner: str | None = Query(
        None,
        description="ISO alpha-2 of exporting country. If omitted, returns MFN + all preferential.",
    ),
    year: int = Query(2024),
    db: Session = Depends(get_db),
):
    rep = db.scalar(select(Country).where(Country.iso_alpha2 == reporter.upper()))
    if not rep:
        raise HTTPException(status_code=404, detail=f"Reporter '{reporter}' not found")

    hs = db.scalar(select(HSCode).where(HSCode.code == hs_code))
    if not hs:
        raise HTTPException(status_code=404, detail=f"HS code '{hs_code}' not found")

    query = select(Tariff).where(
        Tariff.reporter_id == rep.id,
        Tariff.hs_code == hs_code,
        Tariff.year == year,
    )

    par = None
    if partner:
        par = db.scalar(select(Country).where(Country.iso_alpha2 == partner.upper()))
        if not par:
            raise HTTPException(status_code=404, detail=f"Partner '{partner}' not found")
        query = query.where((Tariff.partner_id == par.id) | (Tariff.partner_id.is_(None)))

    rows = db.scalars(query).all()
    if not rows:
        return []

    out: list[TariffOut] = []
    for t in rows:
        partner_country = None
        if t.partner_id:
            pc = db.get(Country, t.partner_id)
            if pc:
                partner_country = CountryOut.model_validate(pc)

        out.append(TariffOut(
            reporter=CountryOut.model_validate(rep),
            partner=partner_country,
            hs_code=t.hs_code,
            year=t.year,
            rate_type=t.rate_type,
            ad_valorem_rate=t.ad_valorem_rate,
            specific_rate=t.specific_rate,
            agreement=t.agreement,
            notes=t.notes,
        ))

    out.sort(key=lambda x: (
        x.ad_valorem_rate if x.ad_valorem_rate is not None else 999.0,
        0 if x.rate_type == "preferential" else 1,
    ))
    return out
