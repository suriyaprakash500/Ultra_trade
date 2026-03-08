"""
Trading Autopilot — Kill Switch.

Emergency stop that immediately closes all positions and halts trading.
Can be triggered manually (from Android app) or automatically by safety layers.
"""

from __future__ import annotations

from datetime import datetime, UTC

from loguru import logger

from backend.risk.safety_layers import get_safety_layers
from backend.trading.paper_trader import get_paper_trader


class KillSwitch:
    """
    Emergency stop controller.

    When activated:
    1. Closes all open positions at market price
    2. Cancels all pending orders
    3. Blocks all new trades via safety Layer 7
    4. Logs the event with reason
    """

    def __init__(self) -> None:
        self._activation_history: list[dict] = []

    async def activate(
        self,
        reason: str = "Manual activation",
        price_map: dict[str, float] | None = None,
    ) -> dict:
        """
        Activate the kill switch.

        Args:
            reason: Why the kill switch was triggered.
            price_map: Current prices for all held symbols.

        Returns:
            dict with details of actions taken.
        """
        logger.critical(f"⚠️ KILL SWITCH ACTIVATED: {reason}")

        safety = get_safety_layers()
        safety.activate_kill_switch(reason)

        trader = get_paper_trader()
        closed_orders = []

        if price_map:
            closed_orders = await trader.close_all_positions(
                price_map=price_map,
                reason=f"Kill switch: {reason}",
            )

        record = {
            "activated_at": datetime.now(UTC).isoformat(),
            "reason": reason,
            "positions_closed": len(closed_orders),
            "orders": closed_orders,
        }
        self._activation_history.append(record)

        return record

    async def deactivate(self) -> dict:
        """
        Deactivate the kill switch and resume trading.

        Returns:
            dict with deactivation confirmation.
        """
        logger.warning("Kill switch deactivated — trading can resume")

        safety = get_safety_layers()
        safety.deactivate_kill_switch()

        return {
            "deactivated_at": datetime.now(UTC).isoformat(),
            "status": "trading_resumed",
        }

    @property
    def is_active(self) -> bool:
        """Check if kill switch is currently active."""
        return get_safety_layers().is_kill_switch_active

    @property
    def history(self) -> list[dict]:
        """Return the history of kill switch activations."""
        return self._activation_history.copy()


# ── Module-level singleton ─────────────────────────────────────────

_kill_switch: KillSwitch | None = None


def get_kill_switch() -> KillSwitch:
    """Return the global KillSwitch singleton."""
    global _kill_switch
    if _kill_switch is None:
        _kill_switch = KillSwitch()
    return _kill_switch
