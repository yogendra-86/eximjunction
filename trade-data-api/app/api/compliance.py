"""Compliance endpoint: required documents for trade corridor + product."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.core.dependencies import require_api_key
from app.db.session import get_db
from app.models import ComplianceDoc, Country, HSCode
from app.schemas.trade import (
    ComplianceDocOut,
    ComplianceResponse,
    CountryOut,
)

router = APIRouter(
    prefix="/compliance",
    tags=["compliance"],
    dependencies=[Depends(require_api_key)],
)


@router.get(
    "",
    response_model=ComplianceResponse,
    summary="Required documents for a trade corridor and product",
)
def get_compliance(
    reporter: str = Query(..., description="ISO alpha-2 of exporter (origin)"),
    partner: str = Query(..., description="ISO alpha-2 of importer (destination)"),
    hs_code: str | None = Query(None, description="Optional HS code for product-specific docs"),
    db: Session = Depends(get_db),
):
    rep = db.scalar(select(Country).where(Country.iso_alpha2 == reporter.upper()))
    if not rep:
        raise HTTPException(status_code=404, detail=f"Reporter '{reporter}' not found")
    par = db.scalar(select(Country).where(Country.iso_alpha2 == partner.upper()))
    if not par:
        raise HTTPException(status_code=404, detail=f"Partner '{partner}' not found")

    if hs_code:
        hs = db.scalar(select(HSCode).where(HSCode.code == hs_code))
        if not hs:
            raise HTTPException(status_code=404, detail=f"HS code '{hs_code}' not found")
        candidate_codes = {hs_code}
        cur = hs
        while cur and cur.parent_code:
            candidate_codes.add(cur.parent_code)
            cur = db.scalar(select(HSCode).where(HSCode.code == cur.parent_code))
    else:
        candidate_codes = set()

    rep_clause = or_(ComplianceDoc.reporter_id.is_(None), ComplianceDoc.reporter_id == rep.id)
    par_clause = or_(ComplianceDoc.partner_id.is_(None), ComplianceDoc.partner_id == par.id)

    if candidate_codes:
        hs_clause = or_(
            ComplianceDoc.hs_code.is_(None),
            ComplianceDoc.hs_code.in_(candidate_codes),
        )
    else:
        hs_clause = ComplianceDoc.hs_code.is_(None)

    docs = db.scalars(
        select(ComplianceDoc).where(rep_clause, par_clause, hs_clause)
    ).all()

    out_docs: list[ComplianceDocOut] = []
    for d in docs:
        rep_c = CountryOut.model_validate(db.get(Country, d.reporter_id)) if d.reporter_id else None
        par_c = CountryOut.model_validate(db.get(Country, d.partner_id)) if d.partner_id else None

        out_docs.append(ComplianceDocOut(
            document_name=d.document_name,
            issuing_authority=d.issuing_authority,
            description=d.description,
            is_mandatory=d.is_mandatory,
            reporter=rep_c,
            partner=par_c,
            hs_code=d.hs_code,
        ))

    out_docs.sort(key=lambda d: (not d.is_mandatory, d.document_name))

    return ComplianceResponse(
        corridor=f"{rep.iso_alpha2} -> {par.iso_alpha2}",
        hs_code=hs_code,
        documents=out_docs,
    )
