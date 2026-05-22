"""Products endpoint: HS code search, detail with hierarchy, top trading partners."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Country, HSCode, TradeFlow
from app.schemas.trade import (
    CountryOut,
    HSCodeDetail,
    HSCodeOut,
    TopPartnersResponse,
    TradePartner,
)

router = APIRouter(prefix="/products", tags=["products"])

@router.get(
    "",
    response_model=list[HSCodeOut],
    summary="List all HS codes with optional filters",
)
def list_all_products(
    level: int | None = Query(None, ge=2, le=6, description="Filter by level: 2=chapter, 4=heading, 6=subheading"),
    parent: str | None = Query(None, description="Filter by parent code, e.g. '09' returns all children of chapter 09"),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0, description="For pagination — skip this many records"),
    db: Session = Depends(get_db),
):
    """
    Returns all HS codes in the database.
    Use `level` to filter by depth, `parent` to get children of a specific code.
    Use `limit` + `offset` for pagination.
    """
    query = select(HSCode).order_by(HSCode.level, HSCode.code)

    if level is not None:
        query = query.where(HSCode.level == level)

    if parent is not None:
        query = query.where(HSCode.parent_code == parent.strip())

    total_query = query  # used for count
    query = query.offset(offset).limit(limit)

    return db.scalars(query).all()


@router.get(
    "/chapters",
    response_model=list[HSCodeOut],
    summary="List all top-level HS chapters (2-digit codes only)",
)
def list_chapters(db: Session = Depends(get_db)):
    """Shortcut for the 97 top-level HS chapters. No parameters needed."""
    return db.scalars(
        select(HSCode).where(HSCode.level == 2).order_by(HSCode.code)
    ).all()

@router.get(
    "/search",
    response_model=list[HSCodeOut],
    summary="Search HS codes by keyword or numeric code",
)
def search_products(
    q: str = Query(..., min_length=1, description="Keyword or partial HS code"),
    level: int | None = Query(None, ge=2, le=6, description="Filter by level (2/4/6)"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """
    If `q` is numeric, matches HS codes that start with that prefix.
    Otherwise does a case-insensitive substring search on description and short_name.
    """
    query = select(HSCode)

    if q.isdigit():
        query = query.where(HSCode.code.startswith(q))
    else:
        like = f"%{q.lower()}%"
        query = query.where(
            func.lower(HSCode.description).like(like)
            | func.lower(func.coalesce(HSCode.short_name, "")).like(like)
        )

    if level is not None:
        query = query.where(HSCode.level == level)

    query = query.order_by(HSCode.level, HSCode.code).limit(limit)
    return db.scalars(query).all()


@router.get(
    "/{hs_code}",
    response_model=HSCodeDetail,
    summary="HS code details with parent chain and immediate children",
)
def get_product(hs_code: str, db: Session = Depends(get_db)):
    hs = db.scalar(select(HSCode).where(HSCode.code == hs_code))
    if not hs:
        raise HTTPException(status_code=404, detail=f"HS code '{hs_code}' not found")

    # Walk up parent chain
    ancestors: list[HSCode] = []
    current = hs
    while current.parent_code:
        parent = db.scalar(select(HSCode).where(HSCode.code == current.parent_code))
        if not parent:
            break
        ancestors.append(parent)
        current = parent
    ancestors.reverse()

    # Immediate children
    children = db.scalars(
        select(HSCode).where(HSCode.parent_code == hs_code).order_by(HSCode.code)
    ).all()

    return HSCodeDetail(
        code=hs.code,
        level=hs.level,
        parent_code=hs.parent_code,
        description=hs.description,
        short_name=hs.short_name,
        ancestors=[HSCodeOut.model_validate(a) for a in ancestors],
        children=[HSCodeOut.model_validate(c) for c in children],
    )


@router.get(
    "/{hs_code}/top-partners",
    response_model=TopPartnersResponse,
    summary="Top trading partners for a product",
)
def top_partners(
    hs_code: str,
    flow: str = Query("export", pattern="^(import|export)$"),
    year: int = Query(2024, ge=1990, le=2030),
    reporter: str | None = Query(
        None,
        description="ISO alpha-2 of reporting country. If omitted, returns top global exporters/importers across all reporters.",
    ),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    hs = db.scalar(select(HSCode).where(HSCode.code == hs_code))
    if not hs:
        raise HTTPException(status_code=404, detail=f"HS code '{hs_code}' not found")

    reporter_country: Country | None = None
    if reporter:
        reporter_country = db.scalar(
            select(Country).where(Country.iso_alpha2 == reporter.upper())
        )
        if not reporter_country:
            raise HTTPException(status_code=404, detail=f"Reporter '{reporter}' not found")

    if reporter_country:
        # Reporter-specific: rank partners
        rows = db.execute(
            select(
                Country,
                func.sum(TradeFlow.value_usd).label("value"),
                func.sum(TradeFlow.quantity).label("qty"),
            )
            .join(TradeFlow, TradeFlow.partner_id == Country.id)
            .where(
                TradeFlow.reporter_id == reporter_country.id,
                TradeFlow.hs_code == hs_code,
                TradeFlow.year == year,
                TradeFlow.flow_type == flow,
            )
            .group_by(Country.id)
            .order_by(func.sum(TradeFlow.value_usd).desc())
            .limit(limit)
        ).all()
    else:
        # Global: rank reporters by total flow of this type
        rows = db.execute(
            select(
                Country,
                func.sum(TradeFlow.value_usd).label("value"),
                func.sum(TradeFlow.quantity).label("qty"),
            )
            .join(TradeFlow, TradeFlow.reporter_id == Country.id)
            .where(
                TradeFlow.hs_code == hs_code,
                TradeFlow.year == year,
                TradeFlow.flow_type == flow,
            )
            .group_by(Country.id)
            .order_by(func.sum(TradeFlow.value_usd).desc())
            .limit(limit)
        ).all()

    partners = [
        TradePartner(
            country=CountryOut.model_validate(country),
            value_usd=float(value or 0),
            quantity=float(qty) if qty is not None else None,
            quantity_unit=None,
            rank=i + 1,
        )
        for i, (country, value, qty) in enumerate(rows)
    ]

    return TopPartnersResponse(
        hs_code=hs_code,
        hs_description=hs.description,
        flow_type=flow,
        year=year,
        reporter=CountryOut.model_validate(reporter_country) if reporter_country else None,
        partners=partners,
    )
