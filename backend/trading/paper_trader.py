"""
Trading Autopilot — Paper Trading Simulator.

Simulates a complete trading environment without risking real money.
Maintains a virtual portfolio with cash balance, open positions,
and full order execution simulation using real market prices.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from loguru import logger

from backend.config import get_settings
from backend.data.models import (
    OrderSide,
    OrderStatus,
    OrderType,
    TradingMode,
)


class PaperPosition:
    """A single paper-traded position."""

    def __init__(
        self,
        symbol: str,
        exchange: str,
        quantity: int,
        average_price: float,
        sector: Optional[str] = None,
    ) -> None:
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.average_price = average_price
        self.current_price = average_price
        self.sector = sector
        self.stop_loss: Optional[float] = None
        self.take_profit: Optional[float] = None
        self.opened_at = datetime.utcnow()

    @property
    def market_value(self) -> float:
        """Current market value of this position."""
        return self.quantity * self.current_price

    @property
    def invested_value(self) -> float:
        """Amount invested (cost basis)."""
        return self.quantity * self.average_price

    @property
    def pnl(self) -> float:
        """Unrealized profit/loss in currency."""
        return self.market_value - self.invested_value

    @property
    def pnl_pct(self) -> float:
        """Unrealized P&L as a percentage."""
        if self.invested_value == 0:
            return 0.0
        return (self.pnl / self.invested_value) * 100

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "quantity": self.quantity,
            "average_price": round(self.average_price, 2),
            "current_price": round(self.current_price, 2),
            "pnl": round(self.pnl, 2),
            "pnl_pct": round(self.pnl_pct, 2),
            "market_value": round(self.market_value, 2),
            "invested_value": round(self.invested_value, 2),
            "sector": self.sector,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "opened_at": self.opened_at.isoformat(),
        }


class PaperOrder:
    """A simulated order."""

    def __init__(
        self,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        trigger_price: float = 0.0,
        reason: str = "",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        ai_confidence: float = 0.0,
    ) -> None:
        self.id = str(uuid.uuid4())
        self.symbol = symbol
        self.exchange = exchange
        self.side = side
        self.quantity = quantity
        self.order_type = order_type
        self.price = price
        self.trigger_price = trigger_price
        self.status = OrderStatus.PENDING.value
        self.reason = reason
        self.stop_loss = stop_loss
        self.take_profit = take_profit
        self.ai_confidence = ai_confidence
        self.executed_price: float = 0.0
        self.created_at = datetime.utcnow()
        self.executed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "id": self.id,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "side": self.side,
            "quantity": self.quantity,
            "order_type": self.order_type,
            "price": self.price,
            "status": self.status,
            "reason": self.reason,
            "ai_confidence": self.ai_confidence,
            "stop_loss": self.stop_loss,
            "take_profit": self.take_profit,
            "executed_price": self.executed_price,
            "created_at": self.created_at.isoformat(),
            "executed_at": (
                self.executed_at.isoformat() if self.executed_at else None
            ),
        }


class PaperTrader:
    """
    Paper trading simulator with virtual portfolio management.

    Maintains:
    - Cash balance (starting capital from settings)
    - Open positions (with real-time P&L)
    - Order history
    - Trade history (completed round-trips)
    """

    def __init__(self, starting_capital: Optional[float] = None) -> None:
        settings = get_settings()
        self.starting_capital = starting_capital or settings.paper_trading_capital
        self.cash_balance = self.starting_capital
        self.positions: dict[str, PaperPosition] = {}
        self.orders: list[PaperOrder] = []
        self.trade_history: list[dict] = []
        self._peak_value = self.starting_capital

        self._restored = False
        logger.info(
            f"Paper trader initialized with ₹{self.starting_capital:,.2f} capital"
        )

    async def restore_from_db(self) -> None:
        """Restore state from database after server restart."""
        if self._restored:
            return

        from backend.data.persistence import load_positions, load_trades, load_orders

        try:
            # Restore positions
            saved_positions = await load_positions()
            for p in saved_positions:
                self.positions[p["symbol"]] = PaperPosition(
                    symbol=p["symbol"],
                    exchange=p.get("exchange", "NSE"),
                    quantity=p["quantity"],
                    average_price=p["average_price"],
                    sector=p.get("sector"),
                )
                pos = self.positions[p["symbol"]]
                pos.current_price = p.get("current_price", p["average_price"])
                pos.stop_loss = p.get("stop_loss")
                pos.take_profit = p.get("take_profit")

            # Restore trade history
            self.trade_history = await load_trades()

            # Restore orders
            saved_orders = await load_orders()
            for o in saved_orders:
                order = PaperOrder(
                    symbol=o["symbol"],
                    exchange=o.get("exchange", "NSE"),
                    side=o["side"],
                    quantity=o["quantity"],
                    order_type=o.get("order_type", "MARKET"),
                    price=o.get("price", 0.0),
                    reason=o.get("reason", ""),
                    ai_confidence=o.get("ai_confidence", 0.0),
                )
                order.id = o["id"]
                order.status = o.get("status", "COMPLETED")
                self.orders.append(order)

            # Recalculate cash based on executed trades
            total_invested = sum(p.invested_value for p in self.positions.values())
            realized_pnl = sum(t.get("pnl", 0) for t in self.trade_history)
            self.cash_balance = self.starting_capital - total_invested + realized_pnl

            self._restored = True
            logger.info(
                f"Restored from DB: {len(self.positions)} positions, "
                f"{len(self.trade_history)} trades, cash=₹{self.cash_balance:,.2f}"
            )
        except Exception as exc:
            logger.error(f"Failed to restore from DB: {exc}")
            self._restored = True

    # ── Portfolio Properties ───────────────────────────────────────

    @property
    def total_invested(self) -> float:
        """Total value invested in positions."""
        return sum(p.invested_value for p in self.positions.values())

    @property
    def total_market_value(self) -> float:
        """Total current market value of all positions."""
        return sum(p.market_value for p in self.positions.values())

    @property
    def portfolio_value(self) -> float:
        """Total portfolio value = cash + market value of positions."""
        return self.cash_balance + self.total_market_value

    @property
    def total_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        return self.portfolio_value - self.starting_capital

    @property
    def total_pnl_pct(self) -> float:
        """Total P&L as percentage of starting capital."""
        if self.starting_capital == 0:
            return 0.0
        return (self.total_pnl / self.starting_capital) * 100

    @property
    def drawdown(self) -> float:
        """Current drawdown from peak portfolio value."""
        if self.portfolio_value > self._peak_value:
            self._peak_value = self.portfolio_value
        if self._peak_value == 0:
            return 0.0
        return ((self._peak_value - self.portfolio_value) / self._peak_value) * 100

    @property
    def positions_count(self) -> int:
        """Number of open positions."""
        return len(self.positions)

    # ── Order Execution ────────────────────────────────────────────

    async def place_order(
        self,
        symbol: str,
        exchange: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        reason: str = "",
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None,
        ai_confidence: float = 0.0,
        current_market_price: Optional[float] = None,
    ) -> PaperOrder:
        """
        Place a simulated order and execute it immediately (for MARKET orders).

        Args:
            symbol: Stock symbol (e.g. "RELIANCE")
            exchange: Exchange (e.g. "NSE")
            side: "BUY" or "SELL"
            quantity: Number of shares
            order_type: "MARKET", "LIMIT", "SL", "SL-M"
            price: Limit price (for LIMIT orders)
            reason: Why this trade is being made
            stop_loss: Stop loss price
            take_profit: Take profit target
            ai_confidence: AI confidence score (0-100)
            current_market_price: Current price to simulate execution

        Returns:
            The created PaperOrder.
        """
        order = PaperOrder(
            symbol=symbol,
            exchange=exchange,
            side=side,
            quantity=quantity,
            order_type=order_type,
            price=price,
            reason=reason,
            stop_loss=stop_loss,
            take_profit=take_profit,
            ai_confidence=ai_confidence,
        )
        self.orders.append(order)

        # For MARKET orders, execute immediately at current price
        if order_type == "MARKET" and current_market_price is not None:
            await self._execute_order(order, current_market_price)
        elif order_type == "LIMIT" and price > 0:
            # For LIMIT orders, check if the price matches (simplified)
            if current_market_price and (
                (side == "BUY" and current_market_price <= price)
                or (side == "SELL" and current_market_price >= price)
            ):
                await self._execute_order(order, price)
            else:
                order.status = OrderStatus.OPEN.value
                logger.info(
                    f"[PAPER] Limit order placed: {side} {quantity}x {symbol} "
                    f"@ ₹{price:.2f} (waiting for fill)"
                )
        else:
            # If no market price available, set to open
            order.status = OrderStatus.OPEN.value
            logger.info(
                f"[PAPER] Order placed: {side} {quantity}x {symbol} "
                f"(awaiting market price)"
            )

        return order

    async def _execute_order(
        self, order: PaperOrder, execution_price: float
    ) -> None:
        """Process an order fill at the given price."""
        from backend.data.persistence import save_order, save_position, save_trade, delete_position

        order.executed_price = execution_price
        order.executed_at = datetime.utcnow()
        order.status = OrderStatus.COMPLETED.value

        if order.side == "BUY":
            cost = execution_price * order.quantity
            if cost > self.cash_balance:
                order.status = OrderStatus.REJECTED.value
                logger.warning(
                    f"[PAPER] Order rejected: insufficient funds. "
                    f"Need ₹{cost:,.2f}, have ₹{self.cash_balance:,.2f}"
                )
                return

            self.cash_balance -= cost
            self._add_to_position(order, execution_price)
            logger.info(
                f"[PAPER] BUY executed: {order.quantity}x {order.symbol} "
                f"@ ₹{execution_price:.2f} (total: ₹{cost:,.2f})"
            )

            # Persist to DB
            try:
                await save_order(order.to_dict())
                await save_position(order.symbol, self.positions[order.symbol].to_dict())
            except Exception as e:
                logger.error(f"DB save failed: {e}")

        elif order.side == "SELL":
            pnl = self._remove_from_position(order, execution_price)
            if pnl is not None:
                revenue = execution_price * order.quantity
                self.cash_balance += revenue
                logger.info(
                    f"[PAPER] SELL executed: {order.quantity}x {order.symbol} "
                    f"@ ₹{execution_price:.2f} (P&L: ₹{pnl:,.2f})"
                )

                # Persist to DB
                try:
                    await save_order(order.to_dict())
                    if order.symbol in self.positions:
                        await save_position(order.symbol, self.positions[order.symbol].to_dict())
                    else:
                        await delete_position(order.symbol)
                    if self.trade_history:
                        await save_trade(self.trade_history[-1])
                except Exception as e:
                    logger.error(f"DB save failed: {e}")
            else:
                order.status = OrderStatus.REJECTED.value
                logger.warning(
                    f"[PAPER] SELL rejected: no position in {order.symbol}"
                )

    def _add_to_position(
        self, order: PaperOrder, execution_price: float
    ) -> None:
        """Add shares to an existing position or create a new one."""
        if order.symbol in self.positions:
            pos = self.positions[order.symbol]
            # Calculate new average price
            total_cost = (pos.average_price * pos.quantity) + (
                execution_price * order.quantity
            )
            pos.quantity += order.quantity
            pos.average_price = total_cost / pos.quantity
        else:
            self.positions[order.symbol] = PaperPosition(
                symbol=order.symbol,
                exchange=order.exchange,
                quantity=order.quantity,
                average_price=execution_price,
            )

        # Set stop loss and take profit on the position
        pos = self.positions[order.symbol]
        if order.stop_loss:
            pos.stop_loss = order.stop_loss
        if order.take_profit:
            pos.take_profit = order.take_profit

    def _remove_from_position(
        self, order: PaperOrder, execution_price: float
    ) -> Optional[float]:
        """Remove shares from a position. Returns realized P&L or None."""
        if order.symbol not in self.positions:
            return None

        pos = self.positions[order.symbol]
        if order.quantity > pos.quantity:
            return None

        # Calculate realized P&L for this sale
        pnl = (execution_price - pos.average_price) * order.quantity

        # Record completed trade
        self.trade_history.append({
            "symbol": order.symbol,
            "side": "SELL",
            "quantity": order.quantity,
            "entry_price": pos.average_price,
            "exit_price": execution_price,
            "pnl": round(pnl, 2),
            "pnl_pct": round(
                ((execution_price - pos.average_price) / pos.average_price) * 100, 2
            ),
            "reason": order.reason,
            "ai_confidence": order.ai_confidence,
            "entered_at": pos.opened_at.isoformat(),
            "exited_at": datetime.utcnow().isoformat(),
        })

        pos.quantity -= order.quantity
        if pos.quantity <= 0:
            del self.positions[order.symbol]

        return pnl

    # ── Position Management ────────────────────────────────────────

    def update_prices(self, price_map: dict[str, float]) -> None:
        """
        Update current prices for all positions.

        Args:
            price_map: dict of {symbol: current_price}
        """
        for symbol, price in price_map.items():
            if symbol in self.positions:
                self.positions[symbol].current_price = price

        # Update peak value for drawdown calculation
        if self.portfolio_value > self._peak_value:
            self._peak_value = self.portfolio_value

    async def check_stop_losses(
        self, price_map: dict[str, float]
    ) -> list[dict]:
        """
        Check if any positions have hit their stop loss or take profit.

        Returns a list of triggered exits.
        """
        triggered = []

        for symbol, price in price_map.items():
            if symbol not in self.positions:
                continue

            pos = self.positions[symbol]
            pos.current_price = price

            # Check stop loss
            if pos.stop_loss and price <= pos.stop_loss:
                order = await self.place_order(
                    symbol=symbol,
                    exchange=pos.exchange,
                    side="SELL",
                    quantity=pos.quantity,
                    reason="Stop loss triggered",
                    current_market_price=price,
                )
                triggered.append({
                    "symbol": symbol,
                    "trigger": "stop_loss",
                    "price": price,
                    "order": order.to_dict(),
                })

            # Check take profit
            elif pos.take_profit and price >= pos.take_profit:
                # Sell 50% at take profit (as per strategy doc)
                sell_qty = max(1, pos.quantity // 2)
                order = await self.place_order(
                    symbol=symbol,
                    exchange=pos.exchange,
                    side="SELL",
                    quantity=sell_qty,
                    reason="Take profit triggered (50% exit)",
                    current_market_price=price,
                )
                triggered.append({
                    "symbol": symbol,
                    "trigger": "take_profit",
                    "price": price,
                    "order": order.to_dict(),
                })

        return triggered

    # ── Portfolio Queries ──────────────────────────────────────────

    def get_portfolio_summary(self) -> dict:
        """Return a summary of the current paper portfolio."""
        return {
            "total_value": round(self.portfolio_value, 2),
            "cash_balance": round(self.cash_balance, 2),
            "invested_value": round(self.total_invested, 2),
            "market_value": round(self.total_market_value, 2),
            "total_pnl": round(self.total_pnl, 2),
            "total_pnl_pct": round(self.total_pnl_pct, 2),
            "positions_count": self.positions_count,
            "drawdown": round(self.drawdown, 2),
            "starting_capital": self.starting_capital,
            "trading_mode": TradingMode.PAPER.value,
        }

    def get_all_positions(self) -> list[dict]:
        """Return all open positions as dicts."""
        return [p.to_dict() for p in self.positions.values()]

    def get_order_history(self) -> list[dict]:
        """Return all orders as dicts."""
        return [o.to_dict() for o in self.orders]

    def get_trade_history(self) -> list[dict]:
        """Return completed trade round-trips."""
        return self.trade_history.copy()

    def get_performance_metrics(self) -> dict:
        """Calculate performance metrics from trade history."""
        if not self.trade_history:
            return {
                "total_trades": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
                "total_pnl": 0.0,
            }

        wins = [t for t in self.trade_history if t["pnl"] > 0]
        losses = [t for t in self.trade_history if t["pnl"] <= 0]

        total_wins = sum(t["pnl"] for t in wins) if wins else 0
        total_losses = abs(sum(t["pnl"] for t in losses)) if losses else 0

        return {
            "total_trades": len(self.trade_history),
            "win_count": len(wins),
            "loss_count": len(losses),
            "win_rate": round(
                (len(wins) / len(self.trade_history)) * 100, 2
            ),
            "avg_win": round(total_wins / len(wins), 2) if wins else 0.0,
            "avg_loss": round(
                total_losses / len(losses), 2
            ) if losses else 0.0,
            "profit_factor": round(
                total_wins / total_losses, 2
            ) if total_losses > 0 else float("inf"),
            "largest_win": round(
                max((t["pnl"] for t in wins), default=0), 2
            ),
            "largest_loss": round(
                min((t["pnl"] for t in losses), default=0), 2
            ),
            "total_pnl": round(
                sum(t["pnl"] for t in self.trade_history), 2
            ),
            "max_drawdown": round(self.drawdown, 2),
        }

    # ── Emergency ──────────────────────────────────────────────────

    async def close_all_positions(
        self, price_map: dict[str, float], reason: str = "Emergency close"
    ) -> list[dict]:
        """
        Close all open positions immediately (kill switch).

        Returns list of executed sell orders.
        """
        closed = []
        symbols = list(self.positions.keys())

        for symbol in symbols:
            pos = self.positions[symbol]
            price = price_map.get(symbol, pos.current_price)
            order = await self.place_order(
                symbol=symbol,
                exchange=pos.exchange,
                side="SELL",
                quantity=pos.quantity,
                reason=reason,
                current_market_price=price,
            )
            closed.append(order.to_dict())

        logger.warning(
            f"[PAPER] All positions closed: {len(closed)} orders executed"
        )
        return closed


# ── Module-level singleton ─────────────────────────────────────────

_paper_trader: Optional[PaperTrader] = None


def get_paper_trader() -> PaperTrader:
    """Return the global PaperTrader singleton (lazy-initialized)."""
    global _paper_trader
    if _paper_trader is None:
        _paper_trader = PaperTrader()
    return _paper_trader
