"""Health check endpoint.

Intentionally NOT protected by API key: monitoring tools (k8s liveness
probes, uptime checkers, etc.) need to ping this without credentials.
The response contains no sensitive business data.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.trade import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    return HealthResponse(
        status="ok" if db_ok else "degraded",
        data_mode=settings.DATA_MODE,
        db_ok=db_ok,
        timestamp=datetime.now(timezone.utc),
    )
