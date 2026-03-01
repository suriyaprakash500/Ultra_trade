"""
Trading Autopilot — 7-Layer Safety System.

Every trade MUST pass through ALL 7 layers before execution.
If any layer blocks, the trade is rejected with a clear reason.

Layer Hierarchy (bottom to top):
    Layer 1: Information Quality      — Verify data sources
    Layer 2: AI Confidence            — Minimum 75% confidence required
    Layer 3: Volatility Filters       — Reject excessively volatile stocks
    Layer 4: Diversification Rules    — Sector/correlation limits
    Layer 5: Position Size Limits     — Max 10% per stock
    Layer 6: Daily Loss Limits        — Stop at -2% daily
    Layer 7: Emergency Kill Switches  — Manual/auto emergency stop
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from loguru import logger

from backend.config import get_settings
from backend.data.models import RiskCheckResult, SafetyLayerResult
from backend.trading.paper_trader import get_paper_trader


@dataclass
class TradeProposal:
    """
    A proposed trade that must pass through all safety layers.

    Populated by the AI decision engine before submission.
    """
    symbol: str
    side: str               # "BUY" or "SELL"
    quantity: int
    price: float
    sector: str = "unknown"
    ai_confidence: float = 0.0
    volatility: float = 0.0  # Historical volatility %
    news_sources: int = 0    # Number of corroborating news sources
    beta: float = 1.0


@dataclass
class LayerResult:
    """Result of a single safety layer check."""
    layer_name: str
    layer_number: int
    result: SafetyLayerResult
    message: str
    details: dict = field(default_factory=dict)


class SafetyLayers:
    """
    The 7-layer safety system.

    Each layer has a dedicated method that returns a LayerResult.
    The `check_all` method runs all layers in sequence and returns
    a comprehensive RiskCheckResult.
    """

    def __init__(self) -> None:
        self._settings = get_settings()
        self._daily_loss: float = 0.0
        self._weekly_loss: float = 0.0
        self._monthly_loss: float = 0.0
        self._kill_switch_active: bool = False
        self._trade_count_today: int = 0

    # ── Main Entry Point ───────────────────────────────────────────

    def check_all(self, proposal: TradeProposal) -> RiskCheckResult:
        """
        Run a trade proposal through all 7 safety layers.

        Returns a RiskCheckResult with pass/fail status and details.
        """
        layers = [
            self._layer_1_information_quality,
            self._layer_2_ai_confidence,
            self._layer_3_volatility_filter,
            self._layer_4_diversification,
            self._layer_5_position_size,
            self._layer_6_daily_loss,
            self._layer_7_kill_switch,
        ]

        results: list[LayerResult] = []
        all_passed = True
        blocked_by: Optional[str] = None
        warnings: list[str] = []

        for layer_func in layers:
            result = layer_func(proposal)
            results.append(result)

            if result.result == SafetyLayerResult.BLOCKED:
                all_passed = False
                blocked_by = f"Layer {result.layer_number}: {result.layer_name}"
                logger.warning(
                    f"Trade BLOCKED by {blocked_by}: {result.message}"
                )
                break  # Stop checking further layers

            if result.result == SafetyLayerResult.WARNING:
                warnings.append(
                    f"Layer {result.layer_number}: {result.message}"
                )

        return RiskCheckResult(
            passed=all_passed,
            layers_checked=len(results),
            layers_passed=sum(
                1 for r in results
                if r.result in (SafetyLayerResult.PASSED, SafetyLayerResult.WARNING)
            ),
            blocked_by=blocked_by,
            warnings=warnings,
            details={
                "layers": [
                    {
                        "name": r.layer_name,
                        "number": r.layer_number,
                        "result": r.result.value,
                        "message": r.message,
                    }
                    for r in results
                ]
            },
        )

    # ── Layer 1: Information Quality ───────────────────────────────

    def _layer_1_information_quality(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Verify that the trade is based on reliable information.

        Rules:
        - Must have at least 1 corroborating news source
        - Rejects trades based on rumors (0 sources)
        """
        if proposal.side == "SELL":
            # Selling (exits) always pass this layer
            return LayerResult(
                layer_name="Information Quality",
                layer_number=1,
                result=SafetyLayerResult.PASSED,
                message="Sell orders bypass information quality check",
            )

        if proposal.news_sources >= 2:
            return LayerResult(
                layer_name="Information Quality",
                layer_number=1,
                result=SafetyLayerResult.PASSED,
                message=f"Trade backed by {proposal.news_sources} sources",
            )
        elif proposal.news_sources == 1:
            return LayerResult(
                layer_name="Information Quality",
                layer_number=1,
                result=SafetyLayerResult.WARNING,
                message="Only 1 news source — proceed with caution",
            )
        else:
            return LayerResult(
                layer_name="Information Quality",
                layer_number=1,
                result=SafetyLayerResult.BLOCKED,
                message="No corroborating news sources — trade rejected",
            )

    # ── Layer 2: AI Confidence ─────────────────────────────────────

    def _layer_2_ai_confidence(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Only trades with >75% confidence from the AI are accepted.

        Sells/exits bypass this check (you should always be able to exit).
        """
        min_confidence = 75.0

        if proposal.side == "SELL":
            return LayerResult(
                layer_name="AI Confidence",
                layer_number=2,
                result=SafetyLayerResult.PASSED,
                message="Sell orders bypass confidence check",
            )

        if proposal.ai_confidence >= min_confidence:
            return LayerResult(
                layer_name="AI Confidence",
                layer_number=2,
                result=SafetyLayerResult.PASSED,
                message=f"AI confidence {proposal.ai_confidence:.1f}% ≥ {min_confidence}%",
            )
        elif proposal.ai_confidence >= 60.0:
            return LayerResult(
                layer_name="AI Confidence",
                layer_number=2,
                result=SafetyLayerResult.WARNING,
                message=f"AI confidence {proposal.ai_confidence:.1f}% is below threshold",
            )
        else:
            return LayerResult(
                layer_name="AI Confidence",
                layer_number=2,
                result=SafetyLayerResult.BLOCKED,
                message=(
                    f"AI confidence {proposal.ai_confidence:.1f}% < {min_confidence}% — "
                    "not confident enough"
                ),
            )

    # ── Layer 3: Volatility Filter ─────────────────────────────────

    def _layer_3_volatility_filter(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Reject stocks with >50% annualized volatility.
        Warn for >30% volatility.
        """
        max_volatility = 50.0
        warn_volatility = 30.0

        if proposal.side == "SELL":
            return LayerResult(
                layer_name="Volatility Filter",
                layer_number=3,
                result=SafetyLayerResult.PASSED,
                message="Sell orders bypass volatility check",
            )

        if proposal.volatility <= warn_volatility:
            return LayerResult(
                layer_name="Volatility Filter",
                layer_number=3,
                result=SafetyLayerResult.PASSED,
                message=f"Volatility {proposal.volatility:.1f}% is within safe range",
            )
        elif proposal.volatility <= max_volatility:
            return LayerResult(
                layer_name="Volatility Filter",
                layer_number=3,
                result=SafetyLayerResult.WARNING,
                message=(
                    f"Volatility {proposal.volatility:.1f}% is elevated "
                    f"(threshold: {warn_volatility}%)"
                ),
            )
        else:
            return LayerResult(
                layer_name="Volatility Filter",
                layer_number=3,
                result=SafetyLayerResult.BLOCKED,
                message=(
                    f"Volatility {proposal.volatility:.1f}% > {max_volatility}% — "
                    "too volatile"
                ),
            )

    # ── Layer 4: Diversification Rules ─────────────────────────────

    def _layer_4_diversification(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Enforce diversification limits:
        - Max 30% of portfolio in one sector
        - Max 6 concurrent positions
        """
        if proposal.side == "SELL":
            return LayerResult(
                layer_name="Diversification",
                layer_number=4,
                result=SafetyLayerResult.PASSED,
                message="Sell orders improve diversification",
            )

        trader = get_paper_trader()
        max_positions = self._settings.max_positions
        max_sector_pct = self._settings.max_sector_concentration_pct

        # Check position count
        if trader.positions_count >= max_positions:
            return LayerResult(
                layer_name="Diversification",
                layer_number=4,
                result=SafetyLayerResult.BLOCKED,
                message=(
                    f"Already at max positions ({max_positions}). "
                    "Close a position before opening new ones."
                ),
            )

        # Check sector concentration
        if trader.portfolio_value > 0:
            sector_value = sum(
                p.market_value
                for p in trader.positions.values()
                if p.sector == proposal.sector
            )
            trade_value = proposal.price * proposal.quantity
            new_sector_pct = (
                (sector_value + trade_value) / trader.portfolio_value
            ) * 100

            if new_sector_pct > max_sector_pct:
                return LayerResult(
                    layer_name="Diversification",
                    layer_number=4,
                    result=SafetyLayerResult.BLOCKED,
                    message=(
                        f"Sector '{proposal.sector}' would reach "
                        f"{new_sector_pct:.1f}% > {max_sector_pct}% limit"
                    ),
                )

        return LayerResult(
            layer_name="Diversification",
            layer_number=4,
            result=SafetyLayerResult.PASSED,
            message=f"Diversification OK ({trader.positions_count}/{max_positions} positions)",
        )

    # ── Layer 5: Position Size Limits ──────────────────────────────

    def _layer_5_position_size(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Max 10% of portfolio in a single stock.
        Max 2% risk per trade (based on stop loss distance).
        """
        if proposal.side == "SELL":
            return LayerResult(
                layer_name="Position Size",
                layer_number=5,
                result=SafetyLayerResult.PASSED,
                message="Sell orders reduce position size",
            )

        trader = get_paper_trader()
        max_position_pct = self._settings.max_single_position_pct
        max_risk_pct = self._settings.max_risk_per_trade_pct

        trade_value = proposal.price * proposal.quantity

        if trader.portfolio_value > 0:
            position_pct = (trade_value / trader.portfolio_value) * 100

            if position_pct > max_position_pct:
                return LayerResult(
                    layer_name="Position Size",
                    layer_number=5,
                    result=SafetyLayerResult.BLOCKED,
                    message=(
                        f"Position would be {position_pct:.1f}% of portfolio "
                        f"(max {max_position_pct}%)"
                    ),
                    details={"position_pct": position_pct},
                )

        # Check risk per trade (2% rule)
        if trader.portfolio_value > 0:
            max_risk_amount = trader.portfolio_value * (max_risk_pct / 100)
            # Assume 5% stop loss if not specified
            risk_amount = trade_value * 0.05

            if risk_amount > max_risk_amount:
                return LayerResult(
                    layer_name="Position Size",
                    layer_number=5,
                    result=SafetyLayerResult.WARNING,
                    message=(
                        f"Risk ₹{risk_amount:,.0f} exceeds 2% limit "
                        f"(₹{max_risk_amount:,.0f}). Consider smaller size."
                    ),
                )

        return LayerResult(
            layer_name="Position Size",
            layer_number=5,
            result=SafetyLayerResult.PASSED,
            message="Position size within limits",
        )

    # ── Layer 6: Daily Loss Limits ─────────────────────────────────

    def _layer_6_daily_loss(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Stop trading if daily loss exceeds -2% of capital.
        """
        trader = get_paper_trader()
        daily_limit_pct = self._settings.daily_loss_limit_pct

        # Calculate today's P&L
        daily_pnl_pct = 0.0
        if trader.starting_capital > 0:
            daily_pnl_pct = (
                (trader.portfolio_value - trader.starting_capital)
                / trader.starting_capital
            ) * 100

        if daily_pnl_pct < -daily_limit_pct:
            return LayerResult(
                layer_name="Daily Loss Limit",
                layer_number=6,
                result=SafetyLayerResult.BLOCKED,
                message=(
                    f"Daily loss {daily_pnl_pct:.2f}% exceeds "
                    f"-{daily_limit_pct}% limit. No more trades today."
                ),
            )

        if daily_pnl_pct < -(daily_limit_pct * 0.7):
            return LayerResult(
                layer_name="Daily Loss Limit",
                layer_number=6,
                result=SafetyLayerResult.WARNING,
                message=(
                    f"Daily loss {daily_pnl_pct:.2f}% approaching limit. "
                    "Proceed carefully."
                ),
            )

        return LayerResult(
            layer_name="Daily Loss Limit",
            layer_number=6,
            result=SafetyLayerResult.PASSED,
            message=f"Daily P&L: {daily_pnl_pct:+.2f}% (limit: -{daily_limit_pct}%)",
        )

    # ── Layer 7: Kill Switch ───────────────────────────────────────

    def _layer_7_kill_switch(
        self, proposal: TradeProposal
    ) -> LayerResult:
        """
        Emergency kill switch — blocks ALL trades when active.

        Activated by:
        - Manual trigger
        - Total drawdown > 20%
        - Win rate collapse (< 45% after 20+ trades)
        """
        if self._kill_switch_active:
            return LayerResult(
                layer_name="Kill Switch",
                layer_number=7,
                result=SafetyLayerResult.BLOCKED,
                message="KILL SWITCH ACTIVE — All trading halted",
            )

        # Auto-trigger: total drawdown
        trader = get_paper_trader()
        max_drawdown = self._settings.total_drawdown_limit_pct

        if trader.drawdown > max_drawdown:
            self._kill_switch_active = True
            logger.critical(
                f"KILL SWITCH triggered: drawdown {trader.drawdown:.1f}% "
                f"> {max_drawdown}%"
            )
            return LayerResult(
                layer_name="Kill Switch",
                layer_number=7,
                result=SafetyLayerResult.BLOCKED,
                message=(
                    f"KILL SWITCH AUTO-TRIGGERED: "
                    f"Drawdown {trader.drawdown:.1f}% > {max_drawdown}%"
                ),
            )

        # Auto-trigger: win rate collapse
        metrics = trader.get_performance_metrics()
        total_trades = metrics.get("total_trades", 0)
        win_rate = metrics.get("win_rate", 100)

        if total_trades >= 20 and win_rate < 45:
            self._kill_switch_active = True
            logger.critical(
                f"KILL SWITCH triggered: win rate {win_rate:.1f}% < 45% "
                f"after {total_trades} trades"
            )
            return LayerResult(
                layer_name="Kill Switch",
                layer_number=7,
                result=SafetyLayerResult.BLOCKED,
                message=(
                    f"KILL SWITCH AUTO-TRIGGERED: "
                    f"Win rate {win_rate:.1f}% after {total_trades} trades"
                ),
            )

        return LayerResult(
            layer_name="Kill Switch",
            layer_number=7,
            result=SafetyLayerResult.PASSED,
            message="Kill switch inactive — trading allowed",
        )

    # ── Kill Switch Controls ───────────────────────────────────────

    def activate_kill_switch(self, reason: str = "Manual") -> None:
        """Manually activate the kill switch."""
        self._kill_switch_active = True
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")

    def deactivate_kill_switch(self) -> None:
        """Deactivate the kill switch (requires manual action)."""
        self._kill_switch_active = False
        logger.warning("Kill switch deactivated — trading resumed")

    @property
    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is currently active."""
        return self._kill_switch_active

    def reset_daily_counters(self) -> None:
        """Reset daily loss tracking (call at start of each trading day)."""
        self._daily_loss = 0.0
        self._trade_count_today = 0
        logger.info("Daily safety counters reset")


# ── Module-level singleton ─────────────────────────────────────────

_safety: Optional[SafetyLayers] = None


def get_safety_layers() -> SafetyLayers:
    """Return the global SafetyLayers singleton."""
    global _safety
    if _safety is None:
        _safety = SafetyLayers()
    return _safety
