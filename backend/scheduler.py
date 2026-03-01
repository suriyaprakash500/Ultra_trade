"""
Trading Autopilot — Scheduler.

Automated tasks running on schedule:
- Morning routine at 8:45 AM IST (pre-market analysis)
- Price refresh every 5 min during market hours (9:15 AM - 3:30 PM IST)
- Stop-loss / take-profit checks every 5 min during market hours
- Daily metrics snapshot at 3:45 PM IST
"""

from __future__ import annotations

import asyncio
from datetime import datetime, time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

IST = ZoneInfo("Asia/Kolkata")

# Market hours (IST)
MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

_scheduler: AsyncIOScheduler | None = None


def is_market_hours() -> bool:
    """Check if current time is within Indian market hours."""
    now = datetime.now(IST).time()
    return MARKET_OPEN <= now <= MARKET_CLOSE


async def _run_morning_routine() -> None:
    """Execute the morning pre-market routine."""
    logger.info("⏰ Scheduled: Running morning routine...")
    try:
        from backend.ai.morning_routine import MorningRoutine
        routine = MorningRoutine()
        result = await routine.run()
        logger.info(
            f"Morning routine complete: "
            f"{len(result.get('trade_ideas', []))} ideas generated"
        )
    except Exception as exc:
        logger.error(f"Morning routine failed: {exc}")


async def _refresh_prices() -> None:
    """Update current prices for all open positions."""
    if not is_market_hours():
        return

    try:
        from backend.trading.paper_trader import get_paper_trader
        import yfinance as yf

        trader = get_paper_trader()
        if not trader.positions:
            return

        symbols = list(trader.positions.keys())
        price_map = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.fast_info
                price = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
                if price and price > 0:
                    price_map[symbol] = float(price)
            except Exception:
                pass

        if price_map:
            trader.update_prices(price_map)
            logger.info(f"Prices refreshed for {len(price_map)} positions")

    except Exception as exc:
        logger.error(f"Price refresh failed: {exc}")


async def _check_stop_loss_take_profit() -> None:
    """Check SL/TP triggers for all positions."""
    if not is_market_hours():
        return

    try:
        from backend.trading.paper_trader import get_paper_trader
        import yfinance as yf

        trader = get_paper_trader()
        if not trader.positions:
            return

        # Get fresh prices
        symbols = list(trader.positions.keys())
        price_map = {}

        for symbol in symbols:
            try:
                ticker = yf.Ticker(f"{symbol}.NS")
                info = ticker.fast_info
                price = getattr(info, "last_price", None) or getattr(info, "previous_close", None)
                if price and price > 0:
                    price_map[symbol] = float(price)
            except Exception:
                pass

        if price_map:
            triggered = await trader.check_stop_losses(price_map)
            if triggered:
                logger.warning(
                    f"🚨 {len(triggered)} SL/TP triggered: "
                    f"{[t['symbol'] for t in triggered]}"
                )

    except Exception as exc:
        logger.error(f"SL/TP check failed: {exc}")


async def _save_daily_metrics() -> None:
    """Save end-of-day performance snapshot."""
    try:
        from backend.trading.paper_trader import get_paper_trader
        from backend.data.persistence import save_daily_metrics

        trader = get_paper_trader()
        metrics = trader.get_performance_metrics()
        await save_daily_metrics(
            metrics, trader.portfolio_value, trader.cash_balance
        )
        logger.info("📊 Daily metrics snapshot saved")

    except Exception as exc:
        logger.error(f"Daily metrics save failed: {exc}")


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the scheduler with all jobs."""
    global _scheduler

    scheduler = AsyncIOScheduler(timezone=IST)

    # Morning routine: 8:45 AM IST, Mon-Fri
    scheduler.add_job(
        _run_morning_routine,
        CronTrigger(hour=8, minute=45, day_of_week="mon-fri", timezone=IST),
        id="morning_routine",
        name="Morning Pre-Market Routine",
        replace_existing=True,
    )

    # Price refresh: every 5 min during market hours, Mon-Fri
    scheduler.add_job(
        _refresh_prices,
        CronTrigger(
            minute="*/5", hour="9-15", day_of_week="mon-fri", timezone=IST
        ),
        id="price_refresh",
        name="Price Refresh",
        replace_existing=True,
    )

    # SL/TP checks: every 5 min during market hours, Mon-Fri
    scheduler.add_job(
        _check_stop_loss_take_profit,
        CronTrigger(
            minute="*/5", hour="9-15", day_of_week="mon-fri", timezone=IST
        ),
        id="sl_tp_check",
        name="Stop Loss / Take Profit Check",
        replace_existing=True,
    )

    # Daily metrics: 3:45 PM IST, Mon-Fri
    scheduler.add_job(
        _save_daily_metrics,
        CronTrigger(hour=15, minute=45, day_of_week="mon-fri", timezone=IST),
        id="daily_metrics",
        name="Daily Metrics Snapshot",
        replace_existing=True,
    )

    _scheduler = scheduler
    return scheduler


def get_scheduler() -> AsyncIOScheduler | None:
    """Return the global scheduler instance."""
    return _scheduler
