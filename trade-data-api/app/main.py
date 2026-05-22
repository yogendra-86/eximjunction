"""FastAPI application entrypoint.

Run with:
    uvicorn app.main:app --reload
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, billing, compliance, countries, health, portal, products, tariffs, trade_flows
from app.core.config import settings
from app.db.session import Base, get_engine

logging.basicConfig(level=settings.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Ensure tables exist (no-op if already created)
    try:
        Base.metadata.create_all(get_engine())
    except Exception as e:
        log.warning("Could not create tables at startup: %s", e)
    yield


app = FastAPI(
    title="Trade Data API",
    description=(
        "Databank for international trade: HS code search, top trading partners, "
        "trade trends, tariffs, and compliance documents.\n\n"
        "**Authentication:**\n"
        "- Data endpoints require an API key via `X-API-Key` header\n"
        "- Customer endpoints (`/auth/me`, `/billing/*`) use JWT bearer token from `/auth/login`\n"
        "- Admin endpoints (`/auth/admin/*`) use JWT bearer token from `/auth/admin/login`\n\n"
        "**Pricing:** see `/billing/plans` for available subscription tiers."
    ),
    version="0.3.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
prefix = settings.API_PREFIX
app.include_router(health.router, prefix=prefix)
app.include_router(auth.router, prefix=prefix)
app.include_router(billing.router, prefix=prefix)
app.include_router(countries.router, prefix=prefix)
app.include_router(products.router, prefix=prefix)
app.include_router(trade_flows.router, prefix=prefix)
app.include_router(tariffs.router, prefix=prefix)
app.include_router(compliance.router,       prefix=prefix)
app.include_router(portal.router,          prefix=prefix)


@app.get("/", include_in_schema=False)
def root():
    return {
        "name": "Trade Data API",
        "version": "0.3.0",
        "docs": "/docs",
        "api_prefix": prefix,
        "data_mode": settings.DATA_MODE,
        "razorpay_mode": "live" if settings.razorpay_enabled else "mock",
    }
