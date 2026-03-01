"""
Trading Autopilot — Kite Connect API Client.

Wraps the Kite Connect REST API using httpx for direct HTTP calls.
All methods are paper-trading-aware: when in paper mode they return
mock data instead of hitting the real Kite API.
"""

from __future__ import annotations

from typing import Any, Optional

import httpx
from loguru import logger

from backend.config import get_settings
from backend.kite.auth import get_kite_auth

# Kite Connect API base
KITE_API_BASE = "https://api.kite.trade"


class KiteClient:
    """
    High-level wrapper around the Kite Connect REST API.

    Automatically checks whether the system is in paper or live mode
    and delegates accordingly.
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    def _get_headers(self) -> dict:
        """Build authorization headers for Kite API."""
        auth = get_kite_auth()
        return {
            "X-Kite-Version": "3",
            "Authorization": f"token {self._settings.kite_api_key}:{auth.access_token}",
        }

    @property
    def is_ready(self) -> bool:
        """True if the client is authenticated and available."""
        return get_kite_auth().is_authenticated

    # ── Orders ─────────────────────────────────────────────────────

    async def place_order(
        self,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        product: str = "CNC",
        price: float = 0.0,
        trigger_price: float = 0.0,
    ) -> dict:
        """
        Place an order through Kite Connect.

        In paper mode, returns a simulated order_id.
        """
        if self._settings.is_paper_trading:
            logger.info(
                f"[PAPER] Order: {side} {quantity}x {symbol} @ {order_type}"
            )
            return {"order_id": f"PAPER-{symbol}-{side}"}

        data = {
            "tradingsymbol": symbol,
            "exchange": exchange,
            "transaction_type": side,
            "quantity": quantity,
            "order_type": order_type,
            "product": product,
        }
        if order_type == "LIMIT" and price > 0:
            data["price"] = price
        if order_type in ("SL", "SL-M") and trigger_price > 0:
            data["trigger_price"] = trigger_price

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{KITE_API_BASE}/orders/regular",
                    headers=self._get_headers(),
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

            order_id = result.get("data", {}).get("order_id", "")
            logger.info(f"[LIVE] Order placed: {order_id}")
            return {"order_id": str(order_id)}

        except Exception as exc:
            logger.error(f"Order placement failed: {exc}")
            raise

    async def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None,
    ) -> dict:
        """Modify an existing order."""
        if self._settings.is_paper_trading:
            logger.info(f"[PAPER] Modify order: {order_id}")
            return {"order_id": order_id, "status": "modified"}

        data: dict[str, Any] = {}
        if quantity is not None:
            data["quantity"] = quantity
        if price is not None:
            data["price"] = price
        if trigger_price is not None:
            data["trigger_price"] = trigger_price
        if order_type is not None:
            data["order_type"] = order_type

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.put(
                    f"{KITE_API_BASE}/orders/regular/{order_id}",
                    headers=self._get_headers(),
                    data=data,
                )
                response.raise_for_status()
                result = response.json()

            logger.info(f"[LIVE] Order modified: {order_id}")
            return {"order_id": result.get("data", {}).get("order_id", order_id)}
        except Exception as exc:
            logger.error(f"Order modification failed: {exc}")
            raise

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel an open order."""
        if self._settings.is_paper_trading:
            logger.info(f"[PAPER] Cancel order: {order_id}")
            return {"order_id": order_id, "status": "cancelled"}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.delete(
                    f"{KITE_API_BASE}/orders/regular/{order_id}",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            logger.info(f"[LIVE] Order cancelled: {order_id}")
            return {"order_id": result.get("data", {}).get("order_id", order_id)}
        except Exception as exc:
            logger.error(f"Order cancellation failed: {exc}")
            raise

    # ── Portfolio ───────────────────────────────────────────────────

    async def get_positions(self) -> list[dict]:
        """Fetch current positions from Kite."""
        if self._settings.is_paper_trading:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{KITE_API_BASE}/portfolio/positions",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            return result.get("data", {}).get("net", [])
        except Exception as exc:
            logger.error(f"Failed to fetch positions: {exc}")
            return []

    async def get_holdings(self) -> list[dict]:
        """Fetch long-term holdings from Kite."""
        if self._settings.is_paper_trading:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{KITE_API_BASE}/portfolio/holdings",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            return result.get("data", [])
        except Exception as exc:
            logger.error(f"Failed to fetch holdings: {exc}")
            return []

    async def get_orders(self) -> list[dict]:
        """Fetch today's orders from Kite."""
        if self._settings.is_paper_trading:
            return []

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{KITE_API_BASE}/orders",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            return result.get("data", [])
        except Exception as exc:
            logger.error(f"Failed to fetch orders: {exc}")
            return []

    async def get_profile(self) -> dict:
        """Fetch the authenticated user's profile."""
        if self._settings.is_paper_trading:
            return {
                "user_name": "Paper Trader",
                "email": "paper@trading.local",
                "broker": "ZERODHA",
            }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{KITE_API_BASE}/user/profile",
                    headers=self._get_headers(),
                )
                response.raise_for_status()
                result = response.json()

            return result.get("data", {})
        except Exception as exc:
            logger.error(f"Failed to fetch profile: {exc}")
            return {}


# ── Module-level singleton ─────────────────────────────────────────

_kite_client = KiteClient()


def get_kite_client() -> KiteClient:
    """Return the global KiteClient singleton."""
    return _kite_client
