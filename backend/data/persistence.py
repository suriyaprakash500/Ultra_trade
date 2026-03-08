"""
Trading Autopilot — Persistence Layer.

Saves and restores paper trader state to/from SQLite database
so the portfolio survives server restarts and Render deploys.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, UTC
from typing import Optional

from loguru import logger
from sqlalchemy import select, delete

from backend.data.database import get_session
from backend.data.models import (
    OrderRecord,
    PositionRecord,
    TradeRecord,
    DailyMetrics,
    OrderSide,
    OrderStatus,
    OrderType,
    TradingMode,
)


async def save_order(order_dict: dict) -> None:
    """Persist an order to the database."""
    async with get_session() as session:
        record = OrderRecord(
            id=order_dict.get("id", str(uuid.uuid4())),
            symbol=order_dict["symbol"],
            exchange=order_dict.get("exchange", "NSE"),
            side=OrderSide(order_dict["side"]),
            order_type=OrderType(order_dict.get("order_type", "MARKET")),
            quantity=order_dict["quantity"],
            price=order_dict.get("price", 0.0),
            status=OrderStatus(order_dict.get("status", "PENDING")),
            reason=order_dict.get("reason", ""),
            ai_confidence=order_dict.get("ai_confidence", 0.0),
            stop_loss=order_dict.get("stop_loss"),
            take_profit=order_dict.get("take_profit"),
            created_at=datetime.fromisoformat(order_dict["created_at"])
            if "created_at" in order_dict else datetime.now(UTC),
        )
        session.add(record)
    logger.debug(f"Saved order {record.id} to DB")


async def save_position(symbol: str, pos_dict: dict) -> None:
    """Save or update a position in the database."""
    async with get_session() as session:
        # Check existing
        result = await session.execute(
            select(PositionRecord).where(PositionRecord.symbol == symbol)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.quantity = pos_dict["quantity"]
            existing.average_price = pos_dict["average_price"]
            existing.current_price = pos_dict["current_price"]
            existing.pnl = pos_dict["pnl"]
            existing.pnl_pct = pos_dict["pnl_pct"]
            existing.stop_loss = pos_dict.get("stop_loss")
            existing.take_profit = pos_dict.get("take_profit")
            existing.updated_at = datetime.now(UTC)
        else:
            record = PositionRecord(
                id=str(uuid.uuid4()),
                symbol=symbol,
                exchange=pos_dict.get("exchange", "NSE"),
                quantity=pos_dict["quantity"],
                average_price=pos_dict["average_price"],
                current_price=pos_dict["current_price"],
                pnl=pos_dict["pnl"],
                pnl_pct=pos_dict["pnl_pct"],
                stop_loss=pos_dict.get("stop_loss"),
                take_profit=pos_dict.get("take_profit"),
            )
            session.add(record)
    logger.debug(f"Saved position {symbol} to DB")


async def delete_position(symbol: str) -> None:
    """Remove a closed position from the database."""
    async with get_session() as session:
        await session.execute(
            delete(PositionRecord).where(PositionRecord.symbol == symbol)
        )
    logger.debug(f"Deleted position {symbol} from DB")


async def save_trade(trade_dict: dict) -> None:
    """Persist a completed trade to the database."""
    async with get_session() as session:
        record = TradeRecord(
            id=str(uuid.uuid4()),
            order_id=trade_dict.get("order_id", ""),
            symbol=trade_dict["symbol"],
            side=OrderSide(trade_dict.get("side", "SELL")),
            quantity=trade_dict["quantity"],
            entry_price=trade_dict["entry_price"],
            exit_price=trade_dict.get("exit_price", 0.0),
            pnl=trade_dict.get("pnl", 0.0),
            pnl_pct=trade_dict.get("pnl_pct", 0.0),
            reason=trade_dict.get("reason", ""),
            ai_confidence=trade_dict.get("ai_confidence", 0.0),
            entered_at=datetime.fromisoformat(trade_dict["entered_at"])
            if "entered_at" in trade_dict else datetime.now(UTC),
            exited_at=datetime.fromisoformat(trade_dict["exited_at"])
            if "exited_at" in trade_dict else datetime.now(UTC),
        )
        session.add(record)
    logger.debug(f"Saved trade {record.symbol} to DB")


async def load_positions() -> list[dict]:
    """Load all positions from database."""
    async with get_session() as session:
        result = await session.execute(select(PositionRecord))
        positions = result.scalars().all()
        return [
            {
                "symbol": p.symbol,
                "exchange": p.exchange,
                "quantity": p.quantity,
                "average_price": p.average_price,
                "current_price": p.current_price,
                "sector": p.sector,
                "stop_loss": p.stop_loss,
                "take_profit": p.take_profit,
                "opened_at": p.opened_at.isoformat() if p.opened_at else "",
            }
            for p in positions
        ]


async def load_trades() -> list[dict]:
    """Load all completed trades from database."""
    async with get_session() as session:
        result = await session.execute(
            select(TradeRecord).order_by(TradeRecord.exited_at.desc())
        )
        trades = result.scalars().all()
        return [
            {
                "symbol": t.symbol,
                "side": t.side.value if t.side else "SELL",
                "quantity": t.quantity,
                "entry_price": t.entry_price,
                "exit_price": t.exit_price or 0.0,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "reason": t.reason or "",
                "ai_confidence": t.ai_confidence,
                "entered_at": t.entered_at.isoformat() if t.entered_at else "",
                "exited_at": t.exited_at.isoformat() if t.exited_at else "",
            }
            for t in trades
        ]


async def load_orders() -> list[dict]:
    """Load recent orders from database."""
    async with get_session() as session:
        result = await session.execute(
            select(OrderRecord).order_by(OrderRecord.created_at.desc()).limit(100)
        )
        orders = result.scalars().all()
        return [
            {
                "id": o.id,
                "symbol": o.symbol,
                "exchange": o.exchange,
                "side": o.side.value if o.side else "BUY",
                "quantity": o.quantity,
                "order_type": o.order_type.value if o.order_type else "MARKET",
                "price": o.price,
                "status": o.status.value if o.status else "PENDING",
                "reason": o.reason or "",
                "ai_confidence": o.ai_confidence,
                "stop_loss": o.stop_loss,
                "take_profit": o.take_profit,
                "executed_price": o.price,
                "created_at": o.created_at.isoformat() if o.created_at else "",
                "executed_at": o.created_at.isoformat() if o.created_at else None,
            }
            for o in orders
        ]


async def save_daily_metrics(metrics: dict, portfolio_value: float, cash: float) -> None:
    """Save daily performance snapshot."""
    today = datetime.now(UTC).strftime("%Y-%m-%d")

    async with get_session() as session:
        result = await session.execute(
            select(DailyMetrics).where(DailyMetrics.date == today)
        )
        existing = result.scalar_one_or_none()

        if existing:
            existing.total_pnl = metrics.get("total_pnl", 0.0)
            existing.win_count = metrics.get("win_count", 0)
            existing.loss_count = metrics.get("loss_count", 0)
            existing.win_rate = metrics.get("win_rate", 0.0)
            existing.portfolio_value = portfolio_value
            existing.cash_balance = cash
            existing.max_drawdown = metrics.get("max_drawdown", 0.0)
        else:
            record = DailyMetrics(
                id=str(uuid.uuid4()),
                date=today,
                total_pnl=metrics.get("total_pnl", 0.0),
                win_count=metrics.get("win_count", 0),
                loss_count=metrics.get("loss_count", 0),
                win_rate=metrics.get("win_rate", 0.0),
                avg_win=metrics.get("avg_win", 0.0),
                avg_loss=metrics.get("avg_loss", 0.0),
                largest_win=metrics.get("largest_win", 0.0),
                largest_loss=metrics.get("largest_loss", 0.0),
                portfolio_value=portfolio_value,
                cash_balance=cash,
                max_drawdown=metrics.get("max_drawdown", 0.0),
                trades_executed=metrics.get("total_trades", 0),
            )
            session.add(record)
    logger.info(f"Daily metrics saved for {today}")
