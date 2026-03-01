"""
Trading Autopilot — Order Manager.

Coordinates order placement between the paper trader and live Kite client.
Adds validation, logging, and database persistence to every order flow.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger

from backend.config import get_settings
from backend.data.models import OrderCreate, OrderSide
from backend.kite.client import get_kite_client
from backend.trading.paper_trader import get_paper_trader


class OrderManager:
    """
    Unified order manager that routes orders to paper or live execution.

    Ensures every order is:
    1. Validated (basic sanity checks)
    2. Logged
    3. Routed to the correct executor
    4. Recorded in history
    """

    def __init__(self) -> None:
        self._settings = get_settings()

    async def submit_order(
        self,
        order: OrderCreate,
        current_market_price: Optional[float] = None,
        ai_confidence: float = 0.0,
    ) -> dict:
        """
        Submit an order for execution.

        Validates the order, then routes it to paper or live execution.

        Args:
            order: The order to submit.
            current_market_price: Current market price for paper execution.
            ai_confidence: AI confidence score (0-100).

        Returns:
            dict with order details and status.
        """
        # ── Validation ─────────────────────────────────────────────
        errors = self._validate_order(order)
        if errors:
            logger.warning(f"Order validation failed: {errors}")
            return {"status": "rejected", "errors": errors}

        logger.info(
            f"Order submitted: {order.side.value} {order.quantity}x "
            f"{order.symbol} @ {order.order_type.value}"
        )

        # ── Route to executor ──────────────────────────────────────
        if self._settings.is_paper_trading:
            return await self._execute_paper(
                order, current_market_price, ai_confidence
            )
        else:
            return await self._execute_live(order)

    async def _execute_paper(
        self,
        order: OrderCreate,
        current_market_price: Optional[float],
        ai_confidence: float,
    ) -> dict:
        """Execute order through the paper trading simulator."""
        trader = get_paper_trader()

        paper_order = await trader.place_order(
            symbol=order.symbol,
            exchange=order.exchange,
            side=order.side.value,
            quantity=order.quantity,
            order_type=order.order_type.value,
            price=order.price,
            reason=order.reason or "",
            stop_loss=order.stop_loss,
            take_profit=order.take_profit,
            ai_confidence=ai_confidence,
            current_market_price=current_market_price,
        )

        return {
            "status": "executed" if paper_order.status == "COMPLETED" else paper_order.status,
            "order_id": paper_order.id,
            "trading_mode": "paper",
            "order": paper_order.to_dict(),
        }

    async def _execute_live(self, order: OrderCreate) -> dict:
        """Execute order through the live Kite Connect API."""
        client = get_kite_client()

        if not client.is_ready:
            return {
                "status": "rejected",
                "errors": ["Kite client not authenticated"],
            }

        try:
            result = await client.place_order(
                symbol=order.symbol,
                exchange=order.exchange,
                side=order.side.value,
                quantity=order.quantity,
                order_type=order.order_type.value,
                product=order.product.value,
                price=order.price,
                trigger_price=order.trigger_price,
            )

            return {
                "status": "submitted",
                "order_id": result["order_id"],
                "trading_mode": "live",
            }

        except Exception as exc:
            logger.error(f"Live order execution failed: {exc}")
            return {"status": "error", "errors": [str(exc)]}

    def _validate_order(self, order: OrderCreate) -> list[str]:
        """
        Basic order validation.

        Returns list of error messages (empty if valid).
        """
        errors: list[str] = []

        if not order.symbol or not order.symbol.strip():
            errors.append("Symbol is required")

        if order.quantity <= 0:
            errors.append("Quantity must be positive")

        if order.order_type.value == "LIMIT" and order.price <= 0:
            errors.append("Limit price must be positive for LIMIT orders")

        if order.order_type.value in ("SL", "SL-M") and order.trigger_price <= 0:
            errors.append(
                "Trigger price must be positive for SL/SL-M orders"
            )

        # Check if trying to sell more than owned (paper mode)
        if (
            self._settings.is_paper_trading
            and order.side == OrderSide.SELL
        ):
            trader = get_paper_trader()
            pos = trader.positions.get(order.symbol)
            if not pos:
                errors.append(f"No position in {order.symbol} to sell")
            elif order.quantity > pos.quantity:
                errors.append(
                    f"Cannot sell {order.quantity} shares, "
                    f"only {pos.quantity} held"
                )

        return errors

    async def cancel_order(self, order_id: str) -> dict:
        """Cancel an open order."""
        if self._settings.is_paper_trading:
            trader = get_paper_trader()
            for order in trader.orders:
                if order.id == order_id and order.status == "OPEN":
                    order.status = "CANCELLED"
                    return {"status": "cancelled", "order_id": order_id}
            return {"status": "not_found", "order_id": order_id}
        else:
            client = get_kite_client()
            return await client.cancel_order(order_id)


# ── Module-level singleton ─────────────────────────────────────────

_order_manager: Optional[OrderManager] = None


def get_order_manager() -> OrderManager:
    """Return the global OrderManager singleton."""
    global _order_manager
    if _order_manager is None:
        _order_manager = OrderManager()
    return _order_manager
