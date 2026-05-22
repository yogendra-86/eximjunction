"""Countries endpoint: list and lookup."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_api_key
from app.db.session import get_db
from app.models import Country
from app.schemas.trade import CountryOut

router = APIRouter(
    prefix="/countries",
    tags=["countries"],
    dependencies=[Depends(require_api_key)],
)


@router.get("", response_model=list[CountryOut], summary="List all supported countries")
def list_countries(db: Session = Depends(get_db)):
    return db.scalars(select(Country).order_by(Country.name)).all()


@router.get(
    "/{iso_code}",
    response_model=CountryOut,
    summary="Lookup country by ISO alpha-2 or alpha-3",
)
def get_country(iso_code: str, db: Session = Depends(get_db)):
    iso = iso_code.upper()
    q = select(Country).where(
        (Country.iso_alpha2 == iso) | (Country.iso_alpha3 == iso)
    )
    country = db.scalar(q)
    if not country:
        raise HTTPException(status_code=404, detail=f"Country '{iso_code}' not found")
    return country
