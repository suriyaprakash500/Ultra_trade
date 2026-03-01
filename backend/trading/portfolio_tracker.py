"""
Trading Autopilot — Portfolio Tracker.

Aggregates portfolio data from paper or live trading, computes performance
metrics, and provides daily snapshots for the performance dashboard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from loguru import logger

from backend.config import get_settings
from backend.trading.paper_trader import get_paper_trader


class PortfolioTracker:
    """
    Tracks portfolio performance over time.

    Collects daily snapshots and computes rolling metrics:
    win rate, Sharpe ratio, max drawdown, profit factor, etc.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._daily_snapshots: list[dict] = []
        self._daily_returns: list[float] = []

    def get_current_portfolio(self) -> dict:
        """
        Return the current portfolio summary.

        Delegates to PaperTrader in paper mode.
        """
        if self._settings.is_paper_trading:
            return get_paper_trader().get_portfolio_summary()

        # Live mode: would aggregate from Kite positions
        return {"trading_mode": "live", "error": "Not implemented for live"}

    def get_positions(self) -> list[dict]:
        """Return all current positions."""
        if self._settings.is_paper_trading:
            return get_paper_trader().get_all_positions()
        return []

    def get_trade_history(self) -> list[dict]:
        """Return completed trades."""
        if self._settings.is_paper_trading:
            return get_paper_trader().get_trade_history()
        return []

    def get_performance_metrics(self) -> dict:
        """Return computed performance metrics."""
        if self._settings.is_paper_trading:
            metrics = get_paper_trader().get_performance_metrics()
            metrics["sharpe_ratio"] = self._calculate_sharpe_ratio()
            return metrics
        return {}

    def take_daily_snapshot(self) -> dict:
        """
        Record a snapshot of today's portfolio state.

        Should be called at market close each day.
        """
        portfolio = self.get_current_portfolio()
        metrics = self.get_performance_metrics()

        snapshot = {
            "date": datetime.utcnow().strftime("%Y-%m-%d"),
            "portfolio_value": portfolio.get("total_value", 0),
            "cash_balance": portfolio.get("cash_balance", 0),
            "total_pnl": portfolio.get("total_pnl", 0),
            "total_pnl_pct": portfolio.get("total_pnl_pct", 0),
            "positions_count": portfolio.get("positions_count", 0),
            "drawdown": portfolio.get("drawdown", 0),
            **metrics,
        }

        self._daily_snapshots.append(snapshot)

        # Track daily return for Sharpe ratio
        if len(self._daily_snapshots) >= 2:
            prev_value = self._daily_snapshots[-2]["portfolio_value"]
            curr_value = snapshot["portfolio_value"]
            if prev_value > 0:
                daily_return = (curr_value - prev_value) / prev_value
                self._daily_returns.append(daily_return)

        logger.info(
            f"Daily snapshot recorded: "
            f"value=₹{snapshot['portfolio_value']:,.2f}, "
            f"P&L=₹{snapshot['total_pnl']:,.2f}"
        )

        return snapshot

    def get_daily_snapshots(self) -> list[dict]:
        """Return all daily snapshots for charting."""
        return self._daily_snapshots.copy()

    def _calculate_sharpe_ratio(self) -> float:
        """
        Calculate annualized Sharpe ratio from daily returns.

        Sharpe = (mean_return - risk_free_rate) / std_dev * sqrt(252)
        Assumes risk-free rate of 6% (India RBI repo rate approx.)
        """
        if len(self._daily_returns) < 5:
            return 0.0

        import numpy as np

        returns = np.array(self._daily_returns)
        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)

        if std_return == 0:
            return 0.0

        risk_free_daily = 0.06 / 252  # ~6% annual risk-free rate
        sharpe = (mean_return - risk_free_daily) / std_return
        annualized_sharpe = sharpe * np.sqrt(252)

        return round(float(annualized_sharpe), 2)


# ── Module-level singleton ─────────────────────────────────────────

_tracker: Optional[PortfolioTracker] = None


def get_portfolio_tracker() -> PortfolioTracker:
    """Return the global PortfolioTracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = PortfolioTracker()
    return _tracker
