"""Test fixtures."""
import json
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import generate_api_key, hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models import (
    AdminUser,
    APIKey,
    ComplianceDoc,
    Country,
    Customer,
    HSCode,
    Plan,
    Subscription,
    Tariff,
    TradeFlow,
)

SEED_DIR = Path(__file__).parent.parent / "app" / "seed"

TEST_ADMIN_EMAIL = "admin@example.com"
TEST_ADMIN_PASSWORD = "admin-password-1234"
TEST_CUSTOMER_EMAIL = "customer@example.com"
TEST_CUSTOMER_PASSWORD = "customer-password-1234"


def _seed_trade(db):
    iso_to_id: dict[str, int] = {}

    for r in json.loads((SEED_DIR / "countries.json").read_text()):
        c = Country(**r)
        db.add(c)
        db.flush()
        iso_to_id[r["iso_alpha2"]] = c.id

    for r in sorted(json.loads((SEED_DIR / "hs_codes.json").read_text()), key=lambda x: x["level"]):
        db.add(HSCode(**r))

    for r in json.loads((SEED_DIR / "trade_flows.json").read_text()):
        rep = iso_to_id.get(r["reporter"])
        par = iso_to_id.get(r["partner"])
        if not (rep and par):
            continue
        db.add(TradeFlow(
            reporter_id=rep, partner_id=par, hs_code=r["hs_code"], year=r["year"],
            flow_type=r["flow_type"], value_usd=r["value_usd"],
        ))

    for r in json.loads((SEED_DIR / "tariffs.json").read_text()):
        rep = iso_to_id.get(r["reporter"])
        if not rep:
            continue
        par = iso_to_id.get(r["partner"]) if r.get("partner") else None
        db.add(Tariff(
            reporter_id=rep, partner_id=par, hs_code=r["hs_code"], year=r["year"],
            rate_type=r["rate_type"], ad_valorem_rate=r.get("ad_valorem_rate"),
            specific_rate=r.get("specific_rate"), agreement=r.get("agreement"), notes=r.get("notes"),
        ))

    for r in json.loads((SEED_DIR / "compliance_docs.json").read_text()):
        rep = iso_to_id.get(r["reporter"]) if r.get("reporter") else None
        par = iso_to_id.get(r["partner"]) if r.get("partner") else None
        db.add(ComplianceDoc(
            reporter_id=rep, partner_id=par, hs_code=r.get("hs_code"),
            document_name=r["document_name"], issuing_authority=r.get("issuing_authority"),
            description=r["description"], is_mandatory=r.get("is_mandatory", True),
        ))

    db.commit()


def _seed_plans(db):
    for r in json.loads((SEED_DIR / "plans.json").read_text()):
        db.add(Plan(
            code=r["code"], name=r["name"], tier=r["tier"], price_inr=r["price_inr"],
            billing_period=r["billing_period"], daily_request_limit=r.get("daily_request_limit"),
            features=json.dumps(r.get("features", [])),
            is_active=r.get("is_active", True), sort_order=r.get("sort_order", 0),
        ))
    db.commit()


def _seed_auth(db):
    admin = AdminUser(
        email=TEST_ADMIN_EMAIL,
        password_hash=hash_password(TEST_ADMIN_PASSWORD),
        is_active=True,
    )
    db.add(admin)

    customer = Customer(
        email=TEST_CUSTOMER_EMAIL,
        password_hash=hash_password(TEST_CUSTOMER_PASSWORD),
        full_name="Test Customer",
        is_active=True,
    )
    db.add(customer)
    db.flush()

    free_plan = db.scalar(select(Plan).where(Plan.code == "free"))
    db.add(Subscription(
        customer_id=customer.id, plan_id=free_plan.id, status="active",
        started_at=datetime.utcnow(),
        current_period_end=datetime.utcnow() + timedelta(days=36500),
    ))

    plaintext_keys = {}
    for tier in ["free", "starter", "pro", "enterprise"]:
        plaintext, prefix, key_hash = generate_api_key()
        db.add(APIKey(
            customer_id=customer.id, key_prefix=prefix, key_hash=key_hash,
            name=f"{tier} key", tier=tier, is_active=True,
        ))
        plaintext_keys[tier] = plaintext

    revoked_plain, revoked_prefix, revoked_hash = generate_api_key()
    db.add(APIKey(
        customer_id=customer.id, key_prefix=revoked_prefix, key_hash=revoked_hash,
        name="Revoked", tier="pro", is_active=False,
    ))
    plaintext_keys["revoked"] = revoked_plain

    db.commit()
    return plaintext_keys


@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    db = TestSession()
    try:
        _seed_trade(db)
        _seed_plans(db)
        keys = _seed_auth(db)
    finally:
        db.close()

    yield engine, TestSession, keys
    engine.dispose()


@pytest.fixture
def client(test_engine):
    _, TestSession, _ = test_engine

    def override_get_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def keys(test_engine):
    _, _, k = test_engine
    return k


@pytest.fixture
def auth_headers(keys):
    return {"X-API-Key": keys["pro"]}


@pytest.fixture
def admin_token(client):
    r = client.post(
        "/api/v1/auth/admin/login",
        json={"email": TEST_ADMIN_EMAIL, "password": TEST_ADMIN_PASSWORD},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def admin_headers(admin_token):
    return {"Authorization": f"Bearer {admin_token}"}


@pytest.fixture
def customer_token(client):
    r = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_CUSTOMER_EMAIL, "password": TEST_CUSTOMER_PASSWORD},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def customer_headers(customer_token):
    return {"Authorization": f"Bearer {customer_token}"}
