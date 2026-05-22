"""Initialize the database: create tables and load seed data."""
import argparse
import json
import logging
import sys
from pathlib import Path

from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import Base, get_engine, get_session_factory
from app.models import (
    AdminUser, Country, HSCode, TradeFlow, Tariff, ComplianceDoc, Plan,PortalPlan,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)

SEED_DIR = Path(__file__).parent.parent / "seed"


def _load_json(name: str):
    return json.loads((SEED_DIR / name).read_text())


def seed_countries(db) -> dict[str, int]:
    rows = _load_json("countries.json")
    iso_to_id: dict[str, int] = {}

    for r in rows:
        existing = db.scalar(select(Country).where(Country.iso_alpha2 == r["iso_alpha2"]))
        if existing:
            iso_to_id[r["iso_alpha2"]] = existing.id
            continue
        c = Country(**r)
        db.add(c)
        db.flush()
        iso_to_id[r["iso_alpha2"]] = c.id

    db.commit()
    log.info("Seeded %d countries", len(iso_to_id))
    return iso_to_id


def seed_hs_codes(db) -> None:
    rows = sorted(_load_json("hs_codes.json"), key=lambda r: r["level"])
    inserted = 0

    for r in rows:
        existing = db.scalar(select(HSCode).where(HSCode.code == r["code"]))
        if existing:
            continue
        db.add(HSCode(**r))
        inserted += 1

    db.commit()
    log.info("Seeded %d HS codes", inserted)


def seed_trade_flows(db, iso_to_id: dict[str, int]) -> None:
    rows = _load_json("trade_flows.json")
    inserted = 0
    skipped = 0

    for r in rows:
        reporter_id = iso_to_id.get(r["reporter"])
        partner_id = iso_to_id.get(r["partner"])
        if not (reporter_id and partner_id):
            skipped += 1
            continue

        existing = db.scalar(
            select(TradeFlow).where(
                TradeFlow.reporter_id == reporter_id,
                TradeFlow.partner_id == partner_id,
                TradeFlow.hs_code == r["hs_code"],
                TradeFlow.year == r["year"],
                TradeFlow.flow_type == r["flow_type"],
            )
        )
        if existing:
            continue

        db.add(TradeFlow(
            reporter_id=reporter_id,
            partner_id=partner_id,
            hs_code=r["hs_code"],
            year=r["year"],
            flow_type=r["flow_type"],
            value_usd=r["value_usd"],
            quantity=r.get("quantity"),
            quantity_unit=r.get("quantity_unit"),
            source="seed",
        ))
        inserted += 1

        if inserted % 200 == 0:
            db.flush()

    db.commit()
    log.info("Seeded %d trade flow rows (skipped %d for missing country mapping)", inserted, skipped)


def seed_tariffs(db, iso_to_id: dict[str, int]) -> None:
    rows = _load_json("tariffs.json")
    inserted = 0

    for r in rows:
        reporter_id = iso_to_id.get(r["reporter"])
        if not reporter_id:
            continue
        partner_id = iso_to_id.get(r["partner"]) if r.get("partner") else None

        # Skip if already exists
        existing = db.scalar(
            select(Tariff).where(
                Tariff.reporter_id == reporter_id,
                Tariff.hs_code == r["hs_code"],
                Tariff.year == r["year"],
                Tariff.rate_type == r["rate_type"],
                Tariff.partner_id == partner_id,
            )
        )
        if existing:
            continue

        db.add(Tariff(
            reporter_id=reporter_id,
            partner_id=partner_id,
            hs_code=r["hs_code"],
            year=r["year"],
            rate_type=r["rate_type"],
            ad_valorem_rate=r.get("ad_valorem_rate"),
            specific_rate=r.get("specific_rate"),
            agreement=r.get("agreement"),
            notes=r.get("notes"),
            source="seed",
        ))
        inserted += 1

    db.commit()
    log.info("Seeded %d tariff rows", inserted)


def seed_compliance(db, iso_to_id: dict[str, int]) -> None:
    rows = _load_json("compliance_docs.json")
    inserted = 0

    for r in rows:
        reporter_id = iso_to_id.get(r["reporter"]) if r.get("reporter") else None
        partner_id = iso_to_id.get(r["partner"]) if r.get("partner") else None

        # Avoid duplicates by document_name + corridor + hs_code
        existing = db.scalar(
            select(ComplianceDoc).where(
                ComplianceDoc.document_name == r["document_name"],
                ComplianceDoc.reporter_id == reporter_id,
                ComplianceDoc.partner_id == partner_id,
                ComplianceDoc.hs_code == r.get("hs_code"),
            )
        )
        if existing:
            continue

        db.add(ComplianceDoc(
            reporter_id=reporter_id,
            partner_id=partner_id,
            hs_code=r.get("hs_code"),
            document_name=r["document_name"],
            issuing_authority=r.get("issuing_authority"),
            description=r["description"],
            is_mandatory=r.get("is_mandatory", True),
        ))
        inserted += 1

    db.commit()
    log.info("Seeded %d compliance doc rows", inserted)


def seed_plans(db) -> None:
    """Seed subscription plans from plans.json (idempotent — updates existing)."""
    rows = _load_json("plans.json")
    inserted, updated = 0, 0

    for r in rows:
        features_json = json.dumps(r.get("features", []))

        existing = db.scalar(select(Plan).where(Plan.code == r["code"]))
        if existing:
            existing.name = r["name"]
            existing.tier = r["tier"]
            existing.price_inr = r["price_inr"]
            existing.billing_period = r["billing_period"]
            existing.daily_request_limit = r.get("daily_request_limit")
            existing.features = features_json
            existing.is_active = r.get("is_active", True)
            existing.sort_order = r.get("sort_order", 0)
            updated += 1
        else:
            db.add(Plan(
                code=r["code"],
                name=r["name"],
                tier=r["tier"],
                price_inr=r["price_inr"],
                billing_period=r["billing_period"],
                daily_request_limit=r.get("daily_request_limit"),
                features=features_json,
                is_active=r.get("is_active", True),
                sort_order=r.get("sort_order", 0),
            ))
            inserted += 1

    db.commit()
    log.info("Seeded %d plans (inserted %d, updated %d)", inserted + updated, inserted, updated)

def seed_portal_plans(db) -> None:
    """Seed portal subscription plans."""
    rows = _load_json("portal_plans.json")
    inserted, updated = 0, 0

    for r in rows:
        features_json = json.dumps(r.get("features", []))
        existing = db.scalar(select(PortalPlan).where(PortalPlan.code == r["code"]))
        if existing:
            existing.name = r["name"]
            existing.price_inr = r["price_inr"]
            existing.billing_period = r["billing_period"]
            existing.records_per_search = r.get("records_per_search")
            existing.can_export_csv = r.get("can_export_csv", False)
            existing.can_export_excel = r.get("can_export_excel", False)
            existing.can_use_api = r.get("can_use_api", False)
            existing.features = features_json
            existing.is_active = r.get("is_active", True)
            existing.sort_order = r.get("sort_order", 0)
            updated += 1
        else:
            db.add(PortalPlan(
                code=r["code"], name=r["name"], price_inr=r["price_inr"],
                billing_period=r["billing_period"],
                records_per_search=r.get("records_per_search"),
                can_export_csv=r.get("can_export_csv", False),
                can_export_excel=r.get("can_export_excel", False),
                can_use_api=r.get("can_use_api", False),
                features=features_json,
                is_active=r.get("is_active", True),
                sort_order=r.get("sort_order", 0),
            ))
            inserted += 1

    db.commit()
    log.info("Seeded %d portal plans (inserted %d, updated %d)", inserted + updated, inserted, updated)


def seed_admin(db) -> None:
    """Bootstrap admin user from .env settings."""
    if not settings.ADMIN_EMAIL or not settings.ADMIN_PASSWORD:
        log.warning("ADMIN_EMAIL/ADMIN_PASSWORD not set; skipping admin bootstrap")
        return

    existing = db.scalar(select(AdminUser).where(AdminUser.email == settings.ADMIN_EMAIL))
    if existing:
        log.info("Admin user already exists: %s", settings.ADMIN_EMAIL)
        return

    db.add(AdminUser(
        email=settings.ADMIN_EMAIL,
        password_hash=hash_password(settings.ADMIN_PASSWORD),
        is_active=True,
    ))
    db.commit()
    log.info("Created admin user: %s", settings.ADMIN_EMAIL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true", help="Drop all tables first")
    parser.add_argument("--skip-seed", action="store_true", help="Create tables but skip seed loading")
    args = parser.parse_args()

    if args.reset:
        log.warning("Dropping all tables")
        Base.metadata.drop_all(get_engine())

    log.info("Creating tables")
    Base.metadata.create_all(get_engine())

    if args.skip_seed:
        log.info("Skipping seed loading")
        return

    db = get_session_factory()()
    try:
        iso_to_id = seed_countries(db)
        seed_hs_codes(db)
        seed_trade_flows(db, iso_to_id)
        seed_tariffs(db, iso_to_id)
        seed_compliance(db, iso_to_id)
        seed_plans(db)
        seed_portal_plans(db)
        seed_admin(db)
        log.info("Database initialized successfully")
    except Exception:
        db.rollback()
        log.exception("Seed failed; rolled back")
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
