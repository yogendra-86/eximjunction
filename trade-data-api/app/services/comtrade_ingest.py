"""Comtrade data ingestion service — uses official comtradeapicall v1.3.1+

Pulls real trade statistics from UN Comtrade and stores in trade_flows table.

Usage:
    python -m app.services.comtrade_ingest                    # full run
    python -m app.services.comtrade_ingest --dry-run          # preview only
    python -m app.services.comtrade_ingest --hs 090111        # one HS code
    python -m app.services.comtrade_ingest --years 2022 2024  # year range
    python -m app.services.comtrade_ingest --api-key KEY      # override .env
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime

from sqlalchemy import select

from app.core.config import settings
from app.db.session import get_engine, get_session_factory, Base
from app.models.trade import Country, TradeFlow
from app.models.portal import DataIngestionLog

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)

# ── Priority HS codes for EximJunction ───────────────────────────────────────
DEFAULT_HS_CODES = [
    "090111",  # Coffee, not roasted
    "090230",  # Black tea
    "100630",  # Milled rice
    "100199",  # Wheat
    "270900",  # Crude petroleum
    "300490",  # Medicaments (pharma)
    "610910",  # Cotton T-shirts
    "710231",  # Rough diamonds
    "851712",  # Mobile phones
    "854231",  # Integrated circuits
    "870323",  # Passenger cars
]

# Top trading nations — M49 codes
# India=356, USA=842, China=156, Germany=276, Japan=392,
# UK=826, UAE=784, Vietnam=704, South Korea=410, Brazil=76
DEFAULT_REPORTERS = [356, 842, 156, 276, 392, 826, 784, 704, 410, 76]

DEFAULT_YEARS = list(range(2019, 2025))  # 2019–2024


class ComtradeIngester:
    def __init__(self, api_key: str, dry_run: bool = False):
        self.api_key    = api_key
        self.dry_run    = dry_run
        self.calls_made = 0
        self.db         = get_session_factory()()
        self._m49_map: dict[int, int] | None = None

    def _get_m49_map(self) -> dict[int, int]:
        if self._m49_map is None:
            rows = self.db.execute(select(Country.m49_code, Country.id)).all()
            self._m49_map = {m49: cid for m49, cid in rows if m49}
        return self._m49_map

    def _fetch_preview(self, hs_code, reporter_m49, year, flow) -> list[dict]:
        """Use previewFinalData — no key needed, max 500 records per call."""
        import comtradeapicall
        flow_code = "X" if flow == "export" else "M"
        try:
            df = comtradeapicall.previewFinalData(
                typeCode     = "C",
                freqCode     = "A",
                clCode       = "HS",
                period       = str(year),
                reporterCode = str(reporter_m49),
                cmdCode      = hs_code,
                flowCode     = flow_code,
                partnerCode  = None,
                partner2Code = None,
                customsCode  = None,
                motCode      = None,
                maxRecords   = 500,
                format_output    = "JSON",
                aggregateBy      = None,
                breakdownMode    = "classic",
                countOnly        = None,
                includeDesc      = True,
            )
            self.calls_made += 1
            if df is None or df.empty:
                return []
            return df.to_dict(orient="records")
        except Exception as e:
            log.error("previewFinalData error HS %s reporter %d: %s", hs_code, reporter_m49, e)
            return []

    def _fetch_full(self, hs_code, reporter_m49, year, flow) -> list[dict]:
        """Use getFinalData — needs API key, up to 100K records per call."""
        import comtradeapicall
        flow_code = "X" if flow == "export" else "M"
        try:
            df = comtradeapicall.getFinalData(
                subscription_key = self.api_key,
                typeCode         = "C",
                freqCode         = "A",
                clCode           = "HS",
                period           = str(year),
                reporterCode     = str(reporter_m49),
                cmdCode          = hs_code,
                flowCode         = flow_code,
                partnerCode      = None,
                partner2Code     = None,
                customsCode      = None,
                motCode          = None,
                maxRecords       = 100000,
                format_output    = "JSON",
                aggregateBy      = None,
                breakdownMode    = "classic",
                countOnly        = None,
                includeDesc      = True,
            )
            self.calls_made += 1
            if df is None or df.empty:
                return []
            return df.to_dict(orient="records")
        except Exception as e:
            log.error("getFinalData error HS %s reporter %d: %s", hs_code, reporter_m49, e)
            return []

    def _fetch(self, hs_code, reporter_m49, year, flow) -> list[dict]:
        """Use full API if key available, else preview."""
        if self.api_key:
            rows = self._fetch_full(hs_code, reporter_m49, year, flow)
        else:
            rows = self._fetch_preview(hs_code, reporter_m49, year, flow)

        if rows:
            log.info("  Fetched %d rows — HS %s reporter %d year %d %s",
                     len(rows), hs_code, reporter_m49, year, flow)
        else:
            log.info("  No data — HS %s reporter %d year %d %s",
                     hs_code, reporter_m49, year, flow)
        return rows

    def _normalize(self, row: dict) -> dict | None:
        m49_map = self._get_m49_map()

        # Handle both camelCase and PascalCase column names
        def get(row, *keys):
            for k in keys:
                if k in row and row[k] is not None:
                    return row[k]
            return None

        reporter_m49 = get(row, "reporterCode", "ReporterCode")
        partner_m49  = get(row, "partnerCode",  "PartnerCode")
        value        = get(row, "primaryValue", "PrimaryValue") or 0
        flow_code    = get(row, "flowCode",     "FlowCode") or ""
        hs_code      = str(get(row, "cmdCode",  "CmdCode") or "")
        year_val     = get(row, "period",       "Period") or 0

        # Skip world/aggregate partner codes
        try:
            partner_m49 = int(partner_m49)
        except (TypeError, ValueError):
            return None
        if partner_m49 in (0, 896, 899, 971, 972):
            return None

        try:
            reporter_m49 = int(reporter_m49)
            year_val     = int(str(year_val)[:4])
            value        = float(value or 0)
        except (TypeError, ValueError):
            return None

        if value <= 0:
            return None

        reporter_id = m49_map.get(reporter_m49)
        partner_id  = m49_map.get(partner_m49)
        if not reporter_id or not partner_id:
            return None

        flow_type = "export" if str(flow_code).upper() in ("X", "EXPORT") else "import"

        return {
            "reporter_id":   reporter_id,
            "partner_id":    partner_id,
            "hs_code":       hs_code,
            "year":          year_val,
            "flow_type":     flow_type,
            "value_usd":     value,
            "quantity":      float(get(row,"qty","Qty") or 0) or None,
            "quantity_unit": get(row, "qtyUnitAbbr", "QtyUnitAbbr"),
            "source":        "comtrade",
        }

    def _upsert(self, n: dict) -> bool:
        existing = self.db.scalar(
            select(TradeFlow).where(
                TradeFlow.reporter_id == n["reporter_id"],
                TradeFlow.partner_id  == n["partner_id"],
                TradeFlow.hs_code     == n["hs_code"],
                TradeFlow.year        == n["year"],
                TradeFlow.flow_type   == n["flow_type"],
            )
        )
        if existing:
            if abs(existing.value_usd - n["value_usd"]) > 1:
                existing.value_usd = n["value_usd"]
                existing.quantity  = n.get("quantity")
                existing.source    = "comtrade"
                return True
            return False
        self.db.add(TradeFlow(**n))
        return True

    def _log_run(self, hs, rep, yr, flow, fetched, inserted, status="success", err=None):
        try:
            existing = self.db.scalar(
                select(DataIngestionLog).where(
                    DataIngestionLog.hs_code      == hs,
                    DataIngestionLog.reporter_m49 == rep,
                    DataIngestionLog.year         == yr,
                    DataIngestionLog.flow_type    == flow,
                )
            )
            if existing:
                existing.records_fetched  = fetched
                existing.records_inserted = inserted
                existing.status           = status
                existing.error_message    = err
                existing.fetched_at       = datetime.utcnow()
            else:
                self.db.add(DataIngestionLog(
                    hs_code=hs, reporter_m49=rep, year=yr, flow_type=flow,
                    records_fetched=fetched, records_inserted=inserted,
                    status=status, error_message=err,
                ))
        except Exception as e:
            log.warning("Could not write ingestion log: %s", e)

    def ingest_one(self, hs_code, reporter_m49, year, flow) -> dict:
        rows = self._fetch(hs_code, reporter_m49, year, flow)
        inserted = 0

        if rows and not self.dry_run:
            for row in rows:
                n = self._normalize(row)
                if n and self._upsert(n):
                    inserted += 1
            self._log_run(hs_code, reporter_m49, year, flow, len(rows), inserted)
            self.db.commit()
        elif not rows and not self.dry_run:
            self._log_run(hs_code, reporter_m49, year, flow, 0, 0, "empty")
            self.db.commit()

        return {"fetched": len(rows), "inserted": inserted}

    def run(self, hs_codes, reporters, years) -> dict:
        combos = [
            (hs, rep, yr, flow)
            for hs   in hs_codes
            for rep  in reporters
            for yr   in years
            for flow in ("export", "import")
        ]

        total_fetched = total_inserted = 0
        mode = "preview (no key)" if not self.api_key else "full API (with key)"
        log.info("Starting ingestion [%s]: %d HS × %d reporters × %d years × 2 flows = %d calls",
                 mode, len(hs_codes), len(reporters), len(years), len(combos))
        if self.dry_run:
            log.info("DRY RUN — no data will be saved")

        for i, (hs, rep, yr, flow) in enumerate(combos):
            log.info("[%d/%d] HS %s | Reporter M49:%d | Year %d | %s",
                     i + 1, len(combos), hs, rep, yr, flow)
            result         = self.ingest_one(hs, rep, yr, flow)
            total_fetched  += result["fetched"]
            total_inserted += result["inserted"]
            time.sleep(0.25)  # polite rate limiting

        summary = {
            "combinations_attempted": len(combos),
            "total_fetched":          total_fetched,
            "total_inserted":         total_inserted,
            "api_calls_made":         self.calls_made,
            "dry_run":                self.dry_run,
        }
        log.info("Ingestion complete:\n%s", json.dumps(summary, indent=2))
        return summary

    def close(self):
        self.db.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest real trade data from UN Comtrade")
    parser.add_argument("--hs",       nargs="+", default=DEFAULT_HS_CODES,
                        help="HS codes to ingest (default: 11 priority codes)")
    parser.add_argument("--reporter", nargs="+", type=int, default=DEFAULT_REPORTERS,
                        help="Reporter M49 codes (default: top 10 trading nations)")
    parser.add_argument("--years",    nargs=2,   type=int, default=[2019, 2024],
                        metavar=("FROM", "TO"),
                        help="Year range inclusive (default: 2019 2024)")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Fetch data but do not save to database")
    parser.add_argument("--api-key",  default=None,
                        help="Override COMTRADE_API_KEY from .env")
    args = parser.parse_args()

    api_key = args.api_key or settings.COMTRADE_API_KEY or ""
    if not api_key:
        log.warning("No API key — using preview mode (max 500 records per call)")
        log.warning("Get a free key at: comtradeplus.un.org → Register → comtrade-v1")

    Base.metadata.create_all(get_engine())

    years    = list(range(args.years[0], args.years[1] + 1))
    ingester = ComtradeIngester(api_key=api_key, dry_run=args.dry_run)
    try:
        ingester.run(hs_codes=args.hs, reporters=args.reporter, years=years)
    finally:
        ingester.close()


if __name__ == "__main__":
    main()