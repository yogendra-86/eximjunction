"""Razorpay payment gateway integration.

Supports two modes:
- LIVE: real Razorpay creds in env -> actual API calls
- MOCK: no creds -> fake orders/payments for local dev

The mock mode lets you build & test the entire payment flow without
ever hitting Razorpay. When you're ready to go live, just add real
credentials to .env and restart.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import secrets
from typing import Any

from app.core.config import settings

log = logging.getLogger(__name__)


class RazorpayClient:
    def __init__(self) -> None:
        self.enabled = settings.razorpay_enabled
        self._client = None
        if self.enabled:
            try:
                import razorpay  # imported lazily so mock mode doesn't require the lib
                self._client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
                )
            except ImportError:
                log.warning("razorpay package not installed; falling back to mock mode")
                self.enabled = False

    @property
    def is_mock(self) -> bool:
        return not self.enabled

    def create_order(self, amount_paise: int, currency: str = "INR", receipt: str | None = None) -> dict[str, Any]:
        """Create a Razorpay order. Returns dict with 'id', 'amount', 'currency', 'status'."""
        if self.is_mock:
            return {
                "id": f"order_mock_{secrets.token_hex(8)}",
                "amount": amount_paise,
                "currency": currency,
                "status": "created",
                "receipt": receipt,
                "mock": True,
            }

        return self._client.order.create({
            "amount": amount_paise,
            "currency": currency,
            "receipt": receipt or f"rcpt_{secrets.token_hex(6)}",
            "payment_capture": 1,
        })

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """Verify the signature returned by Razorpay checkout."""
        if self.is_mock:
            # In mock mode, accept anything that looks plausible
            return all([razorpay_order_id, razorpay_payment_id, razorpay_signature])

        try:
            self._client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature,
            })
            return True
        except Exception as e:
            log.warning("Razorpay signature verification failed: %s", e)
            return False

    def verify_webhook_signature(self, body: bytes, signature: str) -> bool:
        """Verify a Razorpay webhook signature."""
        if not settings.RAZORPAY_WEBHOOK_SECRET:
            log.warning("RAZORPAY_WEBHOOK_SECRET not configured; rejecting webhook")
            return False

        expected = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)

    def fetch_payment(self, payment_id: str) -> dict[str, Any] | None:
        if self.is_mock:
            return {"id": payment_id, "status": "captured", "mock": True}
        try:
            return self._client.payment.fetch(payment_id)
        except Exception as e:
            log.warning("Razorpay payment fetch failed: %s", e)
            return None


# Singleton
razorpay_client = RazorpayClient()
