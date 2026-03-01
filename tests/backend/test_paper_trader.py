"""
Tests for the Paper Trading Simulator.

Validates:
- Order placement (BUY/SELL)
- Position tracking and P&L calculation
- Insufficient funds handling
- Stop loss and take profit triggers
- Portfolio metrics computation
- Kill switch (close all positions)
"""

import pytest
import asyncio
from backend.trading.paper_trader import PaperTrader


@pytest.fixture
def trader():
    """Create a fresh PaperTrader with ₹100,000 capital."""
    return PaperTrader(starting_capital=100_000.0)


class TestPaperTraderBasics:
    """Test basic portfolio operations."""

    def test_initial_state(self, trader: PaperTrader):
        """Verify starting state is correct."""
        assert trader.cash_balance == 100_000.0
        assert trader.portfolio_value == 100_000.0
        assert trader.positions_count == 0
        assert trader.total_pnl == 0.0
        assert trader.drawdown == 0.0

    @pytest.mark.asyncio
    async def test_buy_order(self, trader: PaperTrader):
        """Test buying shares creates a position and deducts cash."""
        order = await trader.place_order(
            symbol="RELIANCE",
            exchange="NSE",
            side="BUY",
            quantity=10,
            current_market_price=2500.0,
            reason="Test buy",
        )

        assert order.status == "COMPLETED"
        assert order.executed_price == 2500.0

        # Cash should be reduced
        assert trader.cash_balance == 75_000.0  # 100K - (10 * 2500)

        # Position should exist
        assert "RELIANCE" in trader.positions
        pos = trader.positions["RELIANCE"]
        assert pos.quantity == 10
        assert pos.average_price == 2500.0

    @pytest.mark.asyncio
    async def test_sell_order(self, trader: PaperTrader):
        """Test selling shares removes position and adds cash."""
        # First buy
        await trader.place_order(
            symbol="TCS",
            exchange="NSE",
            side="BUY",
            quantity=5,
            current_market_price=3500.0,
        )
        cash_after_buy = trader.cash_balance

        # Then sell at higher price
        await trader.place_order(
            symbol="TCS",
            exchange="NSE",
            side="SELL",
            quantity=5,
            current_market_price=3600.0,
        )

        # Position should be removed
        assert "TCS" not in trader.positions

        # Cash should include profit
        expected_cash = cash_after_buy + (5 * 3600.0)
        assert trader.cash_balance == expected_cash

        # Trade history should have the round-trip
        assert len(trader.trade_history) == 1
        trade = trader.trade_history[0]
        assert trade["pnl"] == 500.0  # (3600 - 3500) * 5
        assert trade["pnl_pct"] == pytest.approx(2.86, abs=0.01)

    @pytest.mark.asyncio
    async def test_insufficient_funds(self, trader: PaperTrader):
        """Test that buying more than cash allows is rejected."""
        order = await trader.place_order(
            symbol="RELIANCE",
            exchange="NSE",
            side="BUY",
            quantity=1000,
            current_market_price=2500.0,  # 2,500,000 > 100,000
        )

        assert order.status == "REJECTED"
        assert trader.positions_count == 0

    @pytest.mark.asyncio
    async def test_sell_without_position(self, trader: PaperTrader):
        """Test that selling without a position is rejected."""
        order = await trader.place_order(
            symbol="INFY",
            exchange="NSE",
            side="SELL",
            quantity=10,
            current_market_price=1500.0,
        )

        assert order.status == "REJECTED"


class TestPaperTraderAdvanced:
    """Test advanced features."""

    @pytest.mark.asyncio
    async def test_average_price_on_add(self, trader: PaperTrader):
        """Test averaging when adding to an existing position."""
        await trader.place_order(
            symbol="RELIANCE",
            exchange="NSE",
            side="BUY",
            quantity=10,
            current_market_price=2500.0,
        )

        await trader.place_order(
            symbol="RELIANCE",
            exchange="NSE",
            side="BUY",
            quantity=10,
            current_market_price=2600.0,
        )

        pos = trader.positions["RELIANCE"]
        assert pos.quantity == 20
        assert pos.average_price == 2550.0  # (25000 + 26000) / 20

    @pytest.mark.asyncio
    async def test_partial_sell(self, trader: PaperTrader):
        """Test selling part of a position."""
        await trader.place_order(
            symbol="TCS",
            exchange="NSE",
            side="BUY",
            quantity=20,
            current_market_price=3500.0,
        )

        await trader.place_order(
            symbol="TCS",
            exchange="NSE",
            side="SELL",
            quantity=10,
            current_market_price=3600.0,
        )

        # Should still have 10 shares
        assert "TCS" in trader.positions
        assert trader.positions["TCS"].quantity == 10

    @pytest.mark.asyncio
    async def test_pnl_tracking(self, trader: PaperTrader):
        """Test P&L calculation with price updates."""
        await trader.place_order(
            symbol="INFY",
            exchange="NSE",
            side="BUY",
            quantity=10,
            current_market_price=1500.0,
        )

        # Update price
        trader.update_prices({"INFY": 1600.0})

        pos = trader.positions["INFY"]
        assert pos.pnl == 1000.0  # (1600 - 1500) * 10
        assert pos.pnl_pct == pytest.approx(6.67, abs=0.01)

    @pytest.mark.asyncio
    async def test_stop_loss_trigger(self, trader: PaperTrader):
        """Test automatic stop loss execution."""
        await trader.place_order(
            symbol="RELIANCE",
            exchange="NSE",
            side="BUY",
            quantity=10,
            current_market_price=2500.0,
            stop_loss=2400.0,
        )

        # Price drops below stop loss
        triggered = await trader.check_stop_losses({"RELIANCE": 2350.0})

        assert len(triggered) == 1
        assert triggered[0]["trigger"] == "stop_loss"
        assert "RELIANCE" not in trader.positions

    @pytest.mark.asyncio
    async def test_close_all_positions(self, trader: PaperTrader):
        """Test emergency close all."""
        await trader.place_order(
            symbol="RELIANCE", exchange="NSE", side="BUY",
            quantity=5, current_market_price=2500.0,
        )
        await trader.place_order(
            symbol="TCS", exchange="NSE", side="BUY",
            quantity=5, current_market_price=3500.0,
        )

        assert trader.positions_count == 2

        closed = await trader.close_all_positions(
            price_map={"RELIANCE": 2500.0, "TCS": 3500.0},
            reason="Kill switch test",
        )

        assert len(closed) == 2
        assert trader.positions_count == 0


class TestPerformanceMetrics:
    """Test performance metrics calculations."""

    @pytest.mark.asyncio
    async def test_metrics_after_trades(self, trader: PaperTrader):
        """Test metrics calculation after a series of trades."""
        # Winning trade
        await trader.place_order(
            symbol="RELIANCE", exchange="NSE", side="BUY",
            quantity=10, current_market_price=2500.0,
        )
        await trader.place_order(
            symbol="RELIANCE", exchange="NSE", side="SELL",
            quantity=10, current_market_price=2600.0,
        )

        # Losing trade
        await trader.place_order(
            symbol="TCS", exchange="NSE", side="BUY",
            quantity=5, current_market_price=3500.0,
        )
        await trader.place_order(
            symbol="TCS", exchange="NSE", side="SELL",
            quantity=5, current_market_price=3400.0,
        )

        metrics = trader.get_performance_metrics()

        assert metrics["total_trades"] == 2
        assert metrics["win_count"] == 1
        assert metrics["loss_count"] == 1
        assert metrics["win_rate"] == 50.0
        assert metrics["total_pnl"] == 500.0  # +1000 - 500

    def test_empty_metrics(self, trader: PaperTrader):
        """Test metrics with no trades."""
        metrics = trader.get_performance_metrics()
        assert metrics["total_trades"] == 0
        assert metrics["win_rate"] == 0.0
