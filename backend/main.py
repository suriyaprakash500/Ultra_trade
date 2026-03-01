"""
Trading Autopilot — Main Application Entry Point.

FastAPI application with:
- REST API routes (for Android app)
- MCP Server (for Grok AI tool access)
- Database initialization
- Logging configuration
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.api.routes import router as api_router
from backend.config import get_settings
from backend.data.database import init_database, close_database
from backend.data.models import HealthResponse
from backend.mcp_server.server import get_tool_registry, get_grok_agent

# ── App state ──────────────────────────────────────────────────────
_start_time: float = 0.0


# ── Lifespan ───────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    global _start_time
    _start_time = time.time()

    settings = get_settings()

    # Configure logging
    logger.add(
        "logs/trading_autopilot.log",
        rotation="10 MB",
        retention="30 days",
        level="INFO",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | {message}",
    )

    logger.info("═══════════════════════════════════════════════════")
    logger.info("  Trading Autopilot v0.1.0 — Starting Up")
    logger.info(f"  Mode: {settings.trading_mode.upper()}")
    logger.info(f"  Environment: {settings.app_env}")
    logger.info("═══════════════════════════════════════════════════")

    # Initialize database
    await init_database()

    # Initialize paper trader + restore from DB
    if settings.is_paper_trading:
        from backend.trading.paper_trader import get_paper_trader
        trader = get_paper_trader()
        await trader.restore_from_db()
        logger.info(
            f"Paper trader ready: ₹{trader.cash_balance:,.2f} cash, "
            f"{trader.positions_count} positions"
        )

    # Start scheduler
    from backend.scheduler import create_scheduler
    scheduler = create_scheduler()
    scheduler.start()
    logger.info("Scheduler started with 4 automated jobs ✓")

    logger.info("Application startup complete ✓")

    yield  # App runs here

    # Shutdown
    logger.info("Shutting down...")
    if scheduler.running:
        scheduler.shutdown(wait=False)
    await close_database()
    logger.info("Shutdown complete")


# ── App Creation ───────────────────────────────────────────────────

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title="Trading Autopilot",
        description=(
            "AI-powered trading system with Kite Connect (Zerodha) "
            "integration, 7-layer safety system, and paper trading."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )

    # ── CORS ───────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── REST API routes ────────────────────────────────────────────
    app.include_router(api_router)

    # ── MCP Tool Endpoints ──────────────────────────────────────────
    registry = get_tool_registry()

    @app.get("/mcp/tools")
    async def list_tools() -> dict:
        """List all available MCP tools for Grok AI."""
        return {
            "tools": registry.get_tool_names(),
            "count": len(registry.get_tool_names()),
            "definitions": registry.get_tool_definitions(),
        }

    @app.post("/mcp/chat")
    async def mcp_chat(message: str, system_prompt: str = "") -> dict:
        """
        Chat with the Grok AI agent that has access to all trading tools.

        Grok will autonomously call tools as needed to answer your query.
        """
        agent = get_grok_agent()
        return await agent.chat(
            user_message=message,
            system_prompt=system_prompt,
        )

    # ── Health check (unprotected) ─────────────────────────────────
    @app.get("/health", response_model=HealthResponse)
    async def health_check() -> HealthResponse:
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            trading_mode=settings.trading_mode,
            version="0.1.0",
            uptime_seconds=round(time.time() - _start_time, 2),
        )

    @app.get("/")
    async def root() -> dict:
        """Root endpoint with system info."""
        return {
            "name": "Trading Autopilot",
            "version": "0.1.0",
            "trading_mode": settings.trading_mode,
            "docs": "/docs",
            "health": "/health",
            "mcp": "/mcp",
        }

    return app


# ── Module-level app instance ──────────────────────────────────────
app = create_app()


if __name__ == "__main__":
    import os
    import uvicorn

    settings = get_settings()
    port = int(os.environ.get("PORT", settings.app_port))
    uvicorn.run(
        "backend.main:app",
        host=settings.app_host,
        port=port,
        reload=settings.is_development,
        reload_dirs=["backend"] if settings.is_development else None,
    )
