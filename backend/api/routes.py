"""
Trading Autopilot — REST API Routes.

Endpoints consumed by the Android app for dashboard, trading controls,
news, risk management, and settings.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from backend.api.auth_middleware import require_api_key
from backend.config import get_settings
from backend.data.models import OrderCreate

router = APIRouter(prefix="/api", tags=["Trading API"])


# ═══════════════════════════════════════════════════════════════════
#  Dashboard
# ═══════════════════════════════════════════════════════════════════

@router.get("/dashboard")
async def get_dashboard(_: str = Depends(require_api_key)) -> dict:
    """
    Get complete dashboard data for the Android app.

    Returns portfolio summary, positions, recent trades, and metrics.
    """
    from backend.trading.portfolio_tracker import get_portfolio_tracker
    from backend.trading.paper_trader import get_paper_trader

    tracker = get_portfolio_tracker()
    trader = get_paper_trader()

    return {
        "portfolio": tracker.get_current_portfolio(),
        "positions": tracker.get_positions(),
        "recent_trades": tracker.get_trade_history()[-10:],
        "metrics": tracker.get_performance_metrics(),
        "order_history": trader.get_order_history()[-20:],
    }


# ═══════════════════════════════════════════════════════════════════
#  Portfolio
# ═══════════════════════════════════════════════════════════════════

@router.get("/portfolio")
async def get_portfolio(_: str = Depends(require_api_key)) -> dict:
    """Get current portfolio summary."""
    from backend.trading.portfolio_tracker import get_portfolio_tracker
    return get_portfolio_tracker().get_current_portfolio()


@router.get("/positions")
async def get_positions(_: str = Depends(require_api_key)) -> list:
    """Get all open positions."""
    from backend.trading.portfolio_tracker import get_portfolio_tracker
    return get_portfolio_tracker().get_positions()


@router.get("/trades")
async def get_trades(_: str = Depends(require_api_key)) -> list:
    """Get completed trade history."""
    from backend.trading.portfolio_tracker import get_portfolio_tracker
    return get_portfolio_tracker().get_trade_history()


@router.get("/metrics")
async def get_metrics(_: str = Depends(require_api_key)) -> dict:
    """Get performance metrics."""
    from backend.trading.portfolio_tracker import get_portfolio_tracker
    return get_portfolio_tracker().get_performance_metrics()


# ═══════════════════════════════════════════════════════════════════
#  Trading
# ═══════════════════════════════════════════════════════════════════

@router.post("/orders")
async def place_order(
    order: OrderCreate,
    _: str = Depends(require_api_key),
) -> dict:
    """
    Place a new order (paper or live).

    The order is validated and routed through the risk management system.
    """
    from backend.trading.order_manager import get_order_manager
    from backend.mcp_server.tools.market_tools import fetch_stock_price

    manager = get_order_manager()

    # Fetch current price for paper trading execution
    price_data = await fetch_stock_price(order.symbol)
    current_price = price_data.get("current_price", order.price)

    result = await manager.submit_order(
        order=order,
        current_market_price=current_price if current_price > 0 else None,
    )

    return result


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str,
    _: str = Depends(require_api_key),
) -> dict:
    """Cancel an open order."""
    from backend.trading.order_manager import get_order_manager
    manager = get_order_manager()
    return await manager.cancel_order(order_id)


@router.post("/orders/risk-check")
async def check_risk(
    symbol: str,
    side: str,
    price: float,
    quantity: int = 1,
    ai_confidence: float = 75.0,
    _: str = Depends(require_api_key),
) -> dict:
    """
    Check if a proposed trade passes the 7-layer safety system.

    Does NOT execute the trade — only validates it.
    """
    from backend.risk.safety_layers import get_safety_layers, TradeProposal
    from backend.risk.correlation import get_sector

    proposal = TradeProposal(
        symbol=symbol.upper(),
        side=side.upper(),
        quantity=quantity,
        price=price,
        sector=get_sector(symbol),
        ai_confidence=ai_confidence,
        news_sources=1,
    )

    safety = get_safety_layers()
    result = safety.check_all(proposal)
    return result.model_dump()


# ═══════════════════════════════════════════════════════════════════
#  Market Data
# ═══════════════════════════════════════════════════════════════════

@router.get("/market/price/{symbol}")
async def get_stock_price(
    symbol: str,
    _: str = Depends(require_api_key),
) -> dict:
    """Get current price for a stock."""
    from backend.mcp_server.tools.market_tools import fetch_stock_price
    return await fetch_stock_price(symbol)


@router.get("/market/history/{symbol}")
async def get_stock_history(
    symbol: str,
    period: str = "1mo",
    _: str = Depends(require_api_key),
) -> dict:
    """Get historical price data."""
    from backend.mcp_server.tools.market_tools import fetch_stock_history
    return await fetch_stock_history(symbol, period)


# ═══════════════════════════════════════════════════════════════════
#  AI & News
# ═══════════════════════════════════════════════════════════════════

@router.get("/news")
async def get_news(_: str = Depends(require_api_key)) -> list:
    """Fetch and analyze latest financial news."""
    from backend.ai.news_analyzer import get_news_analyzer

    analyzer = get_news_analyzer()
    raw = await analyzer.fetch_all_news(max_per_source=10)
    return await analyzer.analyze_batch(raw, max_items=20)


@router.post("/ai/morning-routine")
async def run_morning_routine(_: str = Depends(require_api_key)) -> dict:
    """Execute the full morning intelligence routine."""
    from backend.ai.morning_routine import get_morning_routine
    routine = get_morning_routine()
    return await routine.run()


@router.get("/ai/trade-ideas")
async def get_trade_ideas(_: str = Depends(require_api_key)) -> list:
    """Generate AI-powered trade ideas with technical analysis."""
    from backend.ai.news_analyzer import get_news_analyzer
    from backend.ai.decision_engine import get_decision_engine

    analyzer = get_news_analyzer()
    raw = await analyzer.fetch_all_news(max_per_source=10)
    analyses = await analyzer.analyze_batch(raw, max_items=10)

    engine = get_decision_engine()
    ideas = await engine.generate_trade_ideas(news_analyses=analyses)

    # Enrich each idea with technical analysis
    from backend.ai.technical_analysis import get_technical_analysis
    for idea in ideas:
        if isinstance(idea, dict) and "symbol" in idea:
            try:
                ta = await get_technical_analysis(idea["symbol"])
                idea["technical_analysis"] = ta
            except Exception:
                idea["technical_analysis"] = None

    return ideas


@router.get("/market/technical/{symbol}")
async def get_technical(
    symbol: str,
    period: str = "6mo",
    _: str = Depends(require_api_key),
) -> dict:
    """Get full technical analysis for a stock (RSI, MACD, Bollinger, MAs)."""
    from backend.ai.technical_analysis import get_technical_analysis
    return await get_technical_analysis(symbol.upper(), period)


@router.get("/ai/morning-briefing")
async def get_morning_briefing(_: str = Depends(require_api_key)) -> dict:
    """Get the last morning briefing (if available)."""
    from backend.ai.morning_routine import get_morning_routine
    routine = get_morning_routine()
    briefing = routine.last_briefing
    if briefing:
        return briefing
    return {"status": "no_briefing", "message": "Run morning routine first"}


# ═══════════════════════════════════════════════════════════════════
#  Risk Management
# ═══════════════════════════════════════════════════════════════════

@router.post("/risk/kill-switch/activate")
async def activate_kill_switch(
    reason: str = "Manual activation from app",
    _: str = Depends(require_api_key),
) -> dict:
    """Activate the emergency kill switch."""
    from backend.risk.kill_switch import get_kill_switch
    ks = get_kill_switch()
    return await ks.activate(reason=reason)


@router.post("/risk/kill-switch/deactivate")
async def deactivate_kill_switch(
    _: str = Depends(require_api_key),
) -> dict:
    """Deactivate the kill switch and resume trading."""
    from backend.risk.kill_switch import get_kill_switch
    ks = get_kill_switch()
    return await ks.deactivate()


@router.get("/risk/kill-switch/status")
async def kill_switch_status(_: str = Depends(require_api_key)) -> dict:
    """Check if the kill switch is active."""
    from backend.risk.kill_switch import get_kill_switch
    ks = get_kill_switch()
    return {
        "active": ks.is_active,
        "history": ks.history,
    }


@router.get("/scheduler/status")
async def scheduler_status(_: str = Depends(require_api_key)) -> dict:
    """Get scheduler status and upcoming jobs."""
    from backend.scheduler import get_scheduler, is_market_hours

    scheduler = get_scheduler()
    if not scheduler:
        return {"running": False, "jobs": []}

    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run": str(job.next_run_time) if job.next_run_time else None,
        })

    return {
        "running": scheduler.running,
        "market_hours": is_market_hours(),
        "jobs": jobs,
    }


@router.post("/market/refresh-prices")
async def refresh_prices(_: str = Depends(require_api_key)) -> dict:
    """Manually refresh prices for all open positions."""
    from backend.scheduler import _refresh_prices
    await _refresh_prices()

    from backend.trading.paper_trader import get_paper_trader
    trader = get_paper_trader()
    return {
        "positions_updated": trader.positions_count,
        "portfolio_value": round(trader.portfolio_value, 2),
    }


# ═══════════════════════════════════════════════════════════════════
#  Kite Auth
# ═══════════════════════════════════════════════════════════════════

@router.get("/kite/login-url")
async def get_login_url() -> dict:
    """Get the Kite Connect login URL for the Android WebView."""
    from backend.kite.auth import get_kite_auth
    auth = get_kite_auth()
    return {"login_url": auth.login_url}


@router.get("/kite/callback")
async def kite_callback(request_token: str) -> dict:
    """
    Handle the Kite OAuth callback with request_token.

    Exchanges the request_token for an access_token.
    """
    from backend.kite.auth import get_kite_auth
    auth = get_kite_auth()

    try:
        access_token = await auth.exchange_token(request_token)
        return {
            "status": "authenticated",
            "message": "Kite login successful",
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/kite/status")
async def kite_status(_: str = Depends(require_api_key)) -> dict:
    """Check Kite authentication status."""
    from backend.kite.auth import get_kite_auth
    auth = get_kite_auth()
    return {
        "authenticated": auth.is_authenticated,
        "trading_mode": get_settings().trading_mode,
    }
