"""Async client for the UN Comtrade+ API.

Comtrade docs: https://comtradeplus.un.org/
The free tier provides 500 calls/day with an API key. We respect that
by caching every successful response into our local DB so subsequent
queries don't hit the API.

Endpoints used:
    GET /get/C/{frequency}/HS  — preview/data endpoint for goods
        Required params: reporterCode, period, partnerCode, cmdCode, flowCode
"""
import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings

log = logging.getLogger(__name__)


class ComtradeClient:
    """Lightweight async wrapper around Comtrade+. Disabled in mock mode."""

    def __init__(self) -> None:
        self.api_key = settings.COMTRADE_API_KEY
        self.base_url = settings.COMTRADE_BASE_URL.rstrip("/")
        self.enabled = settings.DATA_MODE == "live" and bool(self.api_key)

    async def fetch_trade_flow(
        self,
        reporter_m49: int,
        partner_m49: int | None,
        hs_code: str,
        year: int,
        flow: str,  # 'M' for import, 'X' for export
    ) -> list[dict[str, Any]]:
        """
        Returns raw rows from Comtrade. Empty list if disabled or on error
        (callers should treat empty as "no data" and fall back to mock).
        """
        if not self.enabled:
            return []

        url = f"{self.base_url}/get/C/A/HS"
        params = {
            "reporterCode": reporter_m49,
            "period": year,
            "partnerCode": partner_m49 if partner_m49 is not None else "all",
            "cmdCode": hs_code,
            "flowCode": flow,
            "freqCode": "A",  # annual
        }
        headers = {"Ocp-Apim-Subscription-Key": self.api_key}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 429:
                    log.warning("Comtrade rate-limited; backing off")
                    await asyncio.sleep(2.0)
                    return []
                resp.raise_for_status()
                payload = resp.json()
                return payload.get("data", []) or []
        except httpx.HTTPError as e:
            log.warning("Comtrade fetch failed: %s", e)
            return []

    @staticmethod
    def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
        """Map Comtrade response fields to our internal shape."""
        return {
            "reporter_m49": row.get("reporterCode"),
            "partner_m49": row.get("partnerCode"),
            "hs_code": str(row.get("cmdCode")),
            "year": int(row.get("period", 0)),
            "flow_type": "import" if row.get("flowCode") == "M" else "export",
            "value_usd": float(row.get("primaryValue") or 0.0),
            "quantity": float(row["qty"]) if row.get("qty") else None,
            "quantity_unit": row.get("qtyUnitAbbr"),
        }


# Singleton
comtrade_client = ComtradeClient()
