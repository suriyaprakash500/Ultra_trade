"""
Tests for the Order Manager.

Validates:
- Order validation (symbol, quantity, price, order type)
- Paper mode order routing and execution
- Sell validation (cannot sell more than owned)
- Order cancellation
"""

import pytest
from unittest.mock import patch, MagicMock

from backend.data.models import OrderCreate, OrderSide, OrderType, ProductType
from backend.trading.order_manager import OrderManager
from backend.trading.paper_trader import PaperTrader


@pytest.fixture
def manager():
    """Create a fresh OrderManager with paper trading settings."""
    with patch("backend.trading.order_manager.get_settings") as mock_settings:
        mock_settings.return_value = MagicMock(
            is_paper_trading=True,
            trading_mode="paper",
        )
        return OrderManager()


@pytest.fixture
def paper_trader():
    """Create a test PaperTrader and inject it as the global singleton."""
    trader = PaperTrader(starting_capital=100_000.0)
    with patch("backend.trading.order_manager.get_paper_trader", return_value=trader):
        yield trader


class TestOrderValidation:
    """Test order validation rules."""

    def test_valid_market_buy(self, manager: OrderManager):
        order = OrderCreate(
            symbol="RELIANCE", side=OrderSide.BUY, quantity=10
        )
        errors = manager._validate_order(order)
        assert errors == []

    def test_empty_symbol_rejected(self, manager: OrderManager):
        order = OrderCreate(
            symbol="", side=OrderSide.BUY, quantity=10
        )
        errors = manager._validate_order(order)
        assert any("Symbol" in e for e in errors)

    def test_zero_quantity_rejected(self, manager: OrderManager):
        order = OrderCreate(
            symbol="RELIANCE", side=OrderSide.BUY, quantity=0
        )
        errors = manager._validate_order(order)
        assert any("Quantity" in e or "quantity" in e for e in errors)

    def test_negative_quantity_rejected(self, manager: OrderManager):
        order = OrderCreate(
            symbol="RELIANCE", side=OrderSide.BUY, quantity=-5
        )
        errors = manager._validate_order(order)
        assert any("Quantity" in e or "quantity" in e for e in errors)

    def test_limit_order_without_price_rejected(self, manager: OrderManager):
        order = OrderCreate(
            symbol="RELIANCE",
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.LIMIT,
            price=0.0,
        )
        errors = manager._validate_order(order)
        assert any("price" in e.lower() for e in errors)

    def test_limit_order_with_price_passes(self, manager: OrderManager):
        order = OrderCreate(
            symbol="RELIANCE",
            side=OrderSide.BUY,
            quantity=10,
            order_type=OrderType.LIMIT,
            price=2500.0,
        )
        errors = manager._validate_order(order)
        assert errors == []


class TestPaperOrderExecution:
    """Test order execution in paper mode."""

    @pytest.mark.asyncio
    async def test_buy_order_executed(self, manager: OrderManager, paper_trader: PaperTrader):
        with patch("backend.trading.order_manager.get_paper_trader", return_value=paper_trader):
            order = OrderCreate(
                symbol="RELIANCE", side=OrderSide.BUY, quantity=5
            )
            result = await manager.submit_order(order, current_market_price=2500.0)
            assert result["status"] == "executed"
            assert result["trading_mode"] == "paper"

    @pytest.mark.asyncio
    async def test_sell_no_position_rejected(self, manager: OrderManager, paper_trader: PaperTrader):
        with patch("backend.trading.order_manager.get_paper_trader", return_value=paper_trader):
            order = OrderCreate(
                symbol="INFY", side=OrderSide.SELL, quantity=10
            )
            result = await manager.submit_order(order, current_market_price=1500.0)
            assert result["status"] == "rejected"

    @pytest.mark.asyncio
    async def test_sell_excess_shares_rejected(self, manager: OrderManager, paper_trader: PaperTrader):
        with patch("backend.trading.order_manager.get_paper_trader", return_value=paper_trader):
            # Buy 5 shares first
            await paper_trader.place_order(
                symbol="TCS", exchange="NSE", side="BUY",
                quantity=5, current_market_price=3500.0,
            )

            # Try to sell 10 (more than owned)
            order = OrderCreate(
                symbol="TCS", side=OrderSide.SELL, quantity=10
            )
            result = await manager.submit_order(order, current_market_price=3600.0)
            assert result["status"] == "rejected"


class TestOrderCancellation:
    """Test order cancellation."""

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_order(self, manager: OrderManager, paper_trader: PaperTrader):
        with patch("backend.trading.order_manager.get_paper_trader", return_value=paper_trader):
            result = await manager.cancel_order("nonexistent-id")
            assert result["status"] == "not_found"
