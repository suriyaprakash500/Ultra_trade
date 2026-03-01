# Trading Autopilot — Changelog

All changes to the project are documented here.

---

## [2026-02-28] Session 1 — Project Scaffolding & Backend Foundation

### Created
- **Project structure**: `backend/`, `tests/`, `logs/`, `docs/` directories
- **`backend/requirements.txt`**: All Python dependencies
- **`backend/.env.example`**: Environment variables template
- **`backend/config.py`**: Centralized configuration management with validation
- **`backend/data/models.py`**: SQLAlchemy + Pydantic models (Orders, Positions, Trades, News, Metrics)
- **`backend/data/database.py`**: Async SQLite database setup with session management
- **`backend/main.py`**: FastAPI application entry point with health check
- **`backend/kite/auth.py`**: Kite Connect OAuth flow + token management
- **`backend/kite/client.py`**: Kite API wrapper for orders, positions, holdings
- **`backend/mcp_server/server.py`**: MCP Server setup using FastMCP
- **`backend/mcp_server/tools/trading_tools.py`**: MCP tools for placing/modifying/canceling orders
- **`backend/mcp_server/tools/portfolio_tools.py`**: MCP tools for portfolio, positions, holdings
- **`backend/mcp_server/tools/market_tools.py`**: MCP tools for market data (Yahoo Finance)
- **`backend/mcp_server/tools/analysis_tools.py`**: MCP tools for news analysis via Grok AI
- **`backend/ai/prompts.py`**: Grok AI prompt templates for trading decisions
- **`backend/ai/news_analyzer.py`**: News scraping + Grok-powered sentiment analysis
- **`backend/ai/decision_engine.py`**: Trade idea generation + confidence scoring
- **`backend/ai/morning_routine.py`**: Pre-market intelligence automation
- **`backend/risk/safety_layers.py`**: All 7 safety layers implementation
- **`backend/risk/position_sizer.py`**: Kelly Criterion + max position sizing
- **`backend/risk/kill_switch.py`**: Emergency stop functionality
- **`backend/risk/correlation.py`**: Position correlation management
- **`backend/trading/paper_trader.py`**: Paper trading simulator with virtual portfolio
- **`backend/trading/order_manager.py`**: Order lifecycle management
- **`backend/trading/portfolio_tracker.py`**: P&L and performance metrics tracking
- **`backend/api/routes.py`**: REST API endpoints for Android app
- **`backend/api/auth_middleware.py`**: API key authentication middleware
- **`tests/backend/test_paper_trader.py`**: Unit tests for paper trading
- **`tests/backend/test_risk_layers.py`**: Unit tests for safety layers

---

## [2026-02-28] Session 2 — Python 3.13 Upgrade & Full Integration

### Changed
- **Python upgraded**: 3.9 → 3.13 (venv recreated)
- **`backend/requirements.txt`**: Removed `kiteconnect` SDK (broken on 3.13), using `httpx` instead
- **`backend/kite/auth.py`**: Rewritten to use `httpx` for direct Kite API calls
- **`backend/kite/client.py`**: Rewritten to use `httpx` (orders, positions, holdings, profile)
- **`backend/mcp_server/server.py`**: Replaced `fastmcp` with custom `ToolRegistry` + `GrokToolAgent` using Grok's native OpenAI-compatible function calling — cleaner, no extra dependency
- **`backend/main.py`**: Updated MCP mount to use custom tool registry + /mcp/chat endpoint

### Verified
- All 28 tests pass ✅ (12 paper trader + 16 safety layers)
- Dependencies install cleanly on Python 3.13
- Project structure complete and operational

---

## [2026-03-01] Session 3 — Server Verified & Grok Configured

### Changed
- **`backend/config.py`**: Fixed .env path resolution (uses `Path(__file__).parent / ".env"`)
- **`backend/requirements.txt`**: Added `greenlet>=3.0.0` (required by SQLAlchemy async)
- **`backend/.env`**: Created with Grok API key configured
- **`.gitignore`**: Created to protect API keys and exclude runtime files

### Verified
- Server starts successfully on `http://0.0.0.0:8000`
- Health endpoint: `200 OK` (status: healthy, mode: paper)
- Portfolio endpoint: `₹100,000` paper capital ready
- MCP Tools: All 9 tools registered and accessible at `/mcp/tools`
- Database: All 5 tables initialized (orders, positions, trades, news, daily_metrics)
- Paper trader: Initialized with ₹100,000 capital

---

## [2026-03-01] Session 4 — Android App (Phase 3)

### Created — Android App (`android/`)
- **Gradle**: AGP 8.7.3, Kotlin 2.1, Compose BOM 2024.12, Hilt, Retrofit, KSP
- **Data Layer**:
  - `data/model/Models.kt`: 20+ data classes matching all backend API responses
  - `data/api/TradingApiService.kt`: Retrofit interface with all 20 endpoints
  - `data/repository/TradingRepository.kt`: Repository pattern with Kotlin Result
  - `di/NetworkModule.kt`: Hilt DI with OkHttp (API key interceptor, 120s AI timeout)
- **Theme**:
  - `ui/theme/Color.kt`: Premium dark trading palette (glassmorphic, neon accents)
  - `ui/theme/Theme.kt`: Material 3 dark scheme + custom typography
- **Components**:
  - `ui/components/CommonComponents.kt`: GlassCard, PnlText, SentimentBadge, KillSwitchButton, ConfidenceBar, SectionHeader
- **Screens** (6 total, each with ViewModel + Composable):
  - `ui/dashboard/`: Portfolio card, metrics row, kill switch, positions list
  - `ui/trades/`: AI trade ideas with approve/reject, confidence bars
  - `ui/briefing/`: Market outlook, key events, risk alerts, trade suggestions
  - `ui/news/`: Sentiment feed with impact badges
  - `ui/history/`: Performance summary + trade history with P&L
  - `ui/settings/`: Connection status, backend URL, app info
- **Navigation**: `TradingApp.kt` with 5-tab bottom nav bar
- **Config**: AndroidManifest, ProGuard, strings.xml, gradle-wrapper.properties
