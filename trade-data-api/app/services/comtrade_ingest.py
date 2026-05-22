"""Comtrade data ingestion service.

Pulls real trade statistics from UN Comtrade+ API and stores in trade_flows table.
Respects the 500 calls/day free tier limit via a built-in call counter.

Usage:
    python -m app.services.comtrade_ingest                    # run with defaults
    python -m app.services.comtrade_ingest --hs 090111        # specific HS code
    python -m app.services.comtrade_ingest --hs 090111 300490 # multiple codes
    python -m app.services.comtrade_ingest --reporter IN      # India as reporter
    python -m app.services.comtrade_ingest --years 2019 2024  # year range
    python -m app.services.comtrade_ingest --dry-run          # preview without saving
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.core.config import settings
from app.db.session import get_engine, get_session_factory, Base
from app.models.trade import Country, TradeFlow
from app.models.portal import DataIngestionLog

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

COMTRADE_BASE = "https://comtradeapi.un.org/data/v1"

# Priority HS codes to ingest (highest value for Indian trade)
DEFAULT_HS_CODES = [
    "090111",  # Coffee, not roasted
    "090121",  # Coffee, roasted
    "090230",  # Black tea
    "100630",  # Milled rice
    "100199",  # Wheat
    "270900",  # Crude petroleum
    "271012",  # Light oils / gasoline
    "300490",  # Medicaments, retail
    "610910",  # Cotton T-shirts
    "710231",  # Rough diamonds
    "711319",  # Gold/platinum jewellery
    "847130",  # Laptops/tablets
    "851712",  # Mobile phones
    "854231",  # Integrated circuits
    "870323",  # Passenger cars
]

# Reporter M49 codes for India and major trading partners
INDIA_M49 = 356
DEFAULT_REPORTERS = [356]  # Start with India only

DEFAULT_YEARS = list(range(2019, 2025))  # 2019–2024


class ComtradeIngester:
    def __init__(self, api_key: str, dry_run: bool = False):
        self.api_key   = api_key
        self.dry_run   = dry_run
        self.calls_made = 0
        self.daily_limit = 490  # leave 10 buffer below 500
        self.db        = get_session_factory()()
        self._m49_to_id: dict[int, int] | None = None

    def _build_m49_map(self) -> dict[int, int]:
        """Map M49 codes to our internal country IDs."""
        if self._m49_to_id is not None:
            return self._m49_to_id
        rows = self.db.execute(
            select(Country.m49_code, Country.id)
        ).all()
        self._m49_to_id = {m49: cid for m49, cid in rows}
        return self._m49_to_id

    def _fetch(self, hs_code: str, reporter_m49: int, year: int, flow: str) -> list[dict]:
        """Make one Comtrade API call. Returns list of row dicts."""
        if self.calls_made >= self.daily_limit:
            log.warning("Daily call limit reached (%d). Stopping.", self.daily_limit)
            return []

        url = f"{COMTRADE_BASE}/get/C/A/HS"
        params = {
            "reporterCode": reporter_m49,
            "period": year,
            "partnerCode": "all",  # get all partners in one call
            "cmdCode": hs_code,
            "flowCode": "X" if flow == "export" else "M",
            "freqCode": "A",
            "maxRecords": 500,
        }
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}

        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params=params, headers=headers)
                self.calls_made += 1

                if resp.status_code == 429:
                    log.warning("Rate limited by Comtrade. Sleeping 60s.")
                    time.sleep(60)
                    return []

                if resp.status_code == 403:
                    log.error("Invalid API key or quota exceeded.")
                    return []

                resp.raise_for_status()
                data = resp.json()
                rows = data.get("data", []) or []
                log.info("  Fetched %d rows for HS %s, reporter %d, year %d, flow %s",
                         len(rows), hs_code, reporter_m49, year, flow)
                return rows

        except httpx.HTTPError as e:
            log.error("HTTP error fetching HS %s: %s", hs_code, e)
            return []

    def _normalize(self, row: dict) -> dict | None:
        """Convert Comtrade row to our TradeFlow schema. Returns None to skip."""
        m49_map = self._build_m49_map()

        reporter_m49 = row.get("reporterCode")
        partner_m49  = row.get("partnerCode")

        # Skip aggregate partners (0 = World, 97x = special)
        if partner_m49 in (0, 971, 972, 899):
            return None

        reporter_id = m49_map.get(reporter_m49)
        partner_id  = m49_map.get(partner_m49)

        if not reporter_id or not partner_id:
            return None  # Country not in our DB yet

        value = float(row.get("primaryValue") or 0)
        if value <= 0:
            return None  # Skip zero-value rows

        flow_code = row.get("flowCode", "")
        flow_type = "export" if flow_code == "X" else "import"

        return {
            "reporter_id": reporter_id,
            "partner_id":  partner_id,
            "hs_code":     str(row.get("cmdCode", "")),
            "year":        int(row.get("period", 0)),
            "flow_type":   flow_type,
            "value_usd":   value,
            "quantity":    float(row["qty"]) if row.get("qty") else None,
            "quantity_unit": row.get("qtyUnitAbbr"),
            "source":      "comtrade",
        }

    def _upsert_flow(self, normalized: dict) -> bool:
        """Insert or update a trade flow row. Returns True if inserted/updated."""
        existing = self.db.scalar(
            select(TradeFlow).where(
                TradeFlow.reporter_id == normalized["reporter_id"],
                TradeFlow.partner_id  == normalized["partner_id"],
                TradeFlow.hs_code     == normalized["hs_code"],
                TradeFlow.year        == normalized["year"],
                TradeFlow.flow_type   == normalized["flow_type"],
            )
        )
        if existing:
            # Update if value changed
            if abs(existing.value_usd - normalized["value_usd"]) > 1:
                existing.value_usd   = normalized["value_usd"]
                existing.quantity    = normalized.get("quantity")
                existing.source      = "comtrade"
                return True
            return False
        else:
            self.db.add(TradeFlow(**normalized))
            return True

    def _log_ingestion(self, hs_code: str, reporter_m49: int, year: int,
                       flow: str, fetched: int, inserted: int,
                       status: str = "success", error: str | None = None):
        """Record this ingestion run in data_ingestion_log."""
        # Upsert log record
        existing = self.db.scalar(
            select(DataIngestionLog).where(
                DataIngestionLog.hs_code      == hs_code,
                DataIngestionLog.reporter_m49 == reporter_m49,
                DataIngestionLog.year         == year,
                DataIngestionLog.flow_type    == flow,
            )
        )
        if existing:
            existing.records_fetched  = fetched
            existing.records_inserted = inserted
            existing.status           = status
            existing.error_message    = error
            existing.fetched_at       = datetime.utcnow()
        else:
            self.db.add(DataIngestionLog(
                hs_code=hs_code, reporter_m49=reporter_m49, year=year,
                flow_type=flow, records_fetched=fetched,
                records_inserted=inserted, status=status,
                error_message=error,
            ))

    def ingest_one(self, hs_code: str, reporter_m49: int, year: int, flow: str) -> dict:
        """Fetch and store one HS/reporter/year/flow combination."""
        rows = self._fetch(hs_code, reporter_m49, year, flow)

        if not rows:
            self._log_ingestion(hs_code, reporter_m49, year, flow, 0, 0, "empty")
            self.db.commit()
            return {"fetched": 0, "inserted": 0}

        inserted = 0
        for row in rows:
            normalized = self._normalize(row)
            if normalized is None:
                continue
            if not self.dry_run:
                if self._upsert_flow(normalized):
                    inserted += 1

        if not self.dry_run:
            self._log_ingestion(hs_code, reporter_m49, year, flow, len(rows), inserted)
            self.db.commit()

        return {"fetched": len(rows), "inserted": inserted}

    def run(self, hs_codes: list[str], reporters: list[int], years: list[int]) -> dict:
        """Run ingestion for all combinations. Respects daily limit."""
        total_fetched  = 0
        total_inserted = 0
        combinations   = [
            (hs, rep, yr, flow)
            for hs  in hs_codes
            for rep in reporters
            for yr  in years
            for flow in ("export", "import")
        ]

        log.info("Starting ingestion: %d HS codes × %d reporters × %d years × 2 flows = %d calls",
                 len(hs_codes), len(reporters), len(years), len(combinations))
        log.info("Daily limit: %d calls. Remaining capacity: %d", self.daily_limit, self.daily_limit - self.calls_made)

        if self.dry_run:
            log.info("DRY RUN — no data will be saved")

        for i, (hs, rep, yr, flow) in enumerate(combinations):
            if self.calls_made >= self.daily_limit:
                log.warning("Daily limit reached. Stopping at %d/%d combinations.", i, len(combinations))
                break

            log.info("[%d/%d] HS %s | Reporter M49:%d | Year %d | %s",
                     i + 1, len(combinations), hs, rep, yr, flow)

            result = self.ingest_one(hs, rep, yr, flow)
            total_fetched  += result["fetched"]
            total_inserted += result["inserted"]

            # Brief pause between calls to be respectful to the API
            time.sleep(0.5)

        summary = {
            "combinations_attempted": min(i + 1, len(combinations)),
            "total_fetched":  total_fetched,
            "total_inserted": total_inserted,
            "api_calls_made": self.calls_made,
            "dry_run":        self.dry_run,
        }
        log.info("Ingestion complete: %s", json.dumps(summary, indent=2))
        return summary

    def close(self):
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest real trade data from UN Comtrade+")
    parser.add_argument("--hs", nargs="+", default=DEFAULT_HS_CODES, help="HS codes to ingest")
    parser.add_argument("--reporter", nargs="+", type=int, default=DEFAULT_REPORTERS, help="Reporter M49 codes")
    parser.add_argument("--years", nargs=2, type=int, default=[2019, 2024], metavar=("FROM", "TO"), help="Year range")
    parser.add_argument("--dry-run", action="store_true", help="Fetch but do not save")
    parser.add_argument("--api-key", default=settings.COMTRADE_API_KEY, help="Comtrade API key")
    args = parser.parse_args()

    if not args.api_key:
        log.error("No Comtrade API key. Set COMTRADE_API_KEY in .env or pass --api-key.")
        log.error("Get a free key at: https://comtradeplus.un.org/")
        return

    # Ensure tables exist
    Base.metadata.create_all(get_engine())

    years = list(range(args.years[0], args.years[1] + 1))
    ingester = ComtradeIngester(api_key=args.api_key, dry_run=args.dry_run)
    try:
        ingester.run(hs_codes=args.hs, reporters=args.reporter, years=years)
    finally:
        ingester.close()


if __name__ == "__main__":
    main()
