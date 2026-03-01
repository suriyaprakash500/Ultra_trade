"""
Trading Autopilot — Position Sizer (Kelly Criterion).

Calculates optimal position sizes using the Kelly Criterion formula,
capped by the maximum risk limits from the safety system.

Kelly Criterion:  f* = (bp - q) / b
Where:
    f* = fraction of capital to bet
    b  = net odds (reward/risk ratio)
    p  = probability of winning
    q  = probability of losing (1 - p)
"""

from __future__ import annotations

from loguru import logger

from backend.config import get_settings
from backend.trading.paper_trader import get_paper_trader


class PositionSizer:
    """
    Calculates optimal position sizes using Kelly Criterion.

    Always caps the result at the maximum allowed by risk settings.
    Uses a fractional Kelly (typically 25-50%) for extra safety.
    """

    # Half-Kelly is more conservative and recommended
    KELLY_FRACTION = 0.25  # Quarter-Kelly for extra safety

    def __init__(self) -> None:
        self._settings = get_settings()

    def calculate_kelly_fraction(
        self,
        win_probability: float,
        reward_risk_ratio: float,
    ) -> float:
        """
        Calculate the raw Kelly fraction.

        Args:
            win_probability: Probability of winning (0.0 to 1.0)
            reward_risk_ratio: Expected reward / expected risk

        Returns:
            Kelly fraction (0.0 to 1.0), or 0.0 if the bet is not favorable.
        """
        if reward_risk_ratio <= 0 or win_probability <= 0:
            return 0.0

        p = win_probability
        q = 1 - p
        b = reward_risk_ratio

        kelly = (b * p - q) / b

        # Negative Kelly means don't take the bet
        if kelly <= 0:
            return 0.0

        # Apply fractional Kelly for safety
        return kelly * self.KELLY_FRACTION

    def calculate_position_size(
        self,
        symbol: str,
        entry_price: float,
        stop_loss: float,
        take_profit: float,
        win_probability: float,
    ) -> dict:
        """
        Calculate the recommended position size for a trade.

        Takes into account:
        - Kelly Criterion (optimal fraction)
        - Maximum position size limit (10% of portfolio)
        - Maximum risk per trade (2% of portfolio)

        Args:
            symbol: Stock symbol
            entry_price: Planned entry price
            stop_loss: Stop loss price
            take_profit: Take profit target
            win_probability: AI-estimated win probability (0.0 to 1.0)

        Returns:
            dict with recommended quantity, risk amount, and reasoning.
        """
        trader = get_paper_trader()
        portfolio_value = trader.portfolio_value

        if portfolio_value <= 0 or entry_price <= 0:
            return {
                "symbol": symbol,
                "quantity": 0,
                "reason": "Portfolio value or price is zero",
            }

        # ── Calculate risk/reward ──────────────────────────────────
        risk_per_share = abs(entry_price - stop_loss)
        reward_per_share = abs(take_profit - entry_price)

        if risk_per_share == 0:
            return {
                "symbol": symbol,
                "quantity": 0,
                "reason": "Stop loss equals entry price (zero risk)",
            }

        reward_risk_ratio = reward_per_share / risk_per_share

        # ── Kelly Criterion ────────────────────────────────────────
        kelly_frac = self.calculate_kelly_fraction(
            win_probability, reward_risk_ratio
        )
        kelly_amount = portfolio_value * kelly_frac

        # ── Position size limits ───────────────────────────────────
        max_position_pct = self._settings.max_single_position_pct / 100
        max_position_amount = portfolio_value * max_position_pct

        max_risk_pct = self._settings.max_risk_per_trade_pct / 100
        max_risk_amount = portfolio_value * max_risk_pct
        max_from_risk = (max_risk_amount / risk_per_share) * entry_price

        # ── Cash constraint ────────────────────────────────────────
        max_from_cash = trader.cash_balance

        # ── Final amount: minimum of all constraints ───────────────
        trade_amount = min(
            kelly_amount,
            max_position_amount,
            max_from_risk,
            max_from_cash,
        )

        quantity = max(0, int(trade_amount / entry_price))
        actual_risk = quantity * risk_per_share

        result = {
            "symbol": symbol,
            "quantity": quantity,
            "entry_price": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "risk_per_share": round(risk_per_share, 2),
            "reward_per_share": round(reward_per_share, 2),
            "reward_risk_ratio": round(reward_risk_ratio, 2),
            "kelly_fraction": round(kelly_frac, 4),
            "kelly_amount": round(kelly_amount, 2),
            "max_position_amount": round(max_position_amount, 2),
            "max_risk_amount": round(max_risk_amount, 2),
            "actual_trade_amount": round(quantity * entry_price, 2),
            "actual_risk_amount": round(actual_risk, 2),
            "portfolio_pct": round(
                (quantity * entry_price / portfolio_value) * 100, 2
            ) if portfolio_value > 0 else 0,
        }

        logger.info(
            f"Position sized: {quantity}x {symbol} @ ₹{entry_price:.2f} "
            f"(Kelly: {kelly_frac:.2%}, R:R {reward_risk_ratio:.1f}:1)"
        )

        return result


# ── Module-level singleton ─────────────────────────────────────────

_sizer: PositionSizer | None = None


def get_position_sizer() -> PositionSizer:
    """Return the global PositionSizer singleton."""
    global _sizer
    if _sizer is None:
        _sizer = PositionSizer()
    return _sizer
