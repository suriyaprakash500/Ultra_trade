# Trading Autopilot 🚀

AI-powered stock trading system for Indian equity markets (NSE/BSE) with a 7-layer safety system, paper trading simulator, and real-time Android companion app.

> **⚠️ Paper Trading Mode** — The system runs in paper trading mode by default. No real money is at risk until you explicitly configure live trading with Kite Connect.

---

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Android App (Kotlin/Compose)           │
│  Dashboard │ Trade Ideas │ Briefing │ News │ History      │
└───────────────────────┬──────────────────────────────────┘
                        │ REST API (HTTPS)
┌───────────────────────▼──────────────────────────────────┐
│                 FastAPI Backend (Python 3.13)             │
│                                                          │
│  ┌─────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │ AI/Grok │  │ MCP/Tool │  │  Risk    │  │ Trading  │  │
│  │ Engine  │  │ Registry │  │ 7 Layers │  │ Engine   │  │
│  └────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘  │
│       └──────┬─────┴─────┬───────┘             │         │
│              │           │                      │         │
│  ┌───────────▼───┐  ┌────▼──────┐  ┌───────────▼──────┐  │
│  │ News Analyzer │  │ Scheduler │  │ Paper / Kite     │  │
│  │ + Sentiment   │  │ (5 Jobs)  │  │ Order Execution  │  │
│  └───────────────┘  └───────────┘  └──────────────────┘  │
│                                                          │
│              SQLite (aiosqlite) + SQLAlchemy              │
└──────────────────────────────────────────────────────────┘
        │                                      │
  Yahoo Finance                        Kite Connect API
  (Market Data)                        (Zerodha Broker)
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.13, FastAPI, Uvicorn, SQLAlchemy |
| **AI** | Grok (via Groq API, OpenAI-compatible function calling) |
| **Broker** | Kite Connect (Zerodha) via direct httpx API calls |
| **Market Data** | Yahoo Finance (yfinance) |
| **News** | RSS feeds + BeautifulSoup + AI sentiment analysis |
| **Database** | SQLite (async via aiosqlite) |
| **Scheduler** | APScheduler (5 automated jobs) |
| **Android** | Kotlin 2.1, Jetpack Compose, Material 3, Hilt, Retrofit |
| **Deployment** | Docker → Render (free tier) |

---

## Features

### 🤖 AI-Powered Trading
- **News Sentiment Analysis** — Scrapes financial news from multiple sources, uses Grok AI to analyze sentiment and identify catalysts
- **Trade Idea Generation** — AI generates trade ideas with confidence scores, entry/exit levels, and risk-reward ratios
- **Morning Routine** — Automated pre-market intelligence at 8:45 AM IST
- **Technical Analysis** — RSI, MACD, Bollinger Bands, SMA/EMA, support/resistance levels

### 🛡️ 7-Layer Safety System
1. **Information Quality** — Requires multi-source news verification
2. **AI Confidence** — Blocks trades with low AI confidence (<50%)
3. **Volatility Filter** — Blocks trades in extremely volatile conditions
4. **Position Sizing** — Kelly Criterion + max position limits
5. **Sector Concentration** — Prevents over-exposure to single sectors
6. **Loss Limits** — Daily, weekly, monthly, and total drawdown circuit breakers
7. **Kill Switch** — Emergency stop that closes all positions instantly

### 📊 Paper Trading Simulator
- Virtual portfolio with ₹100,000 starting capital
- Full order lifecycle (BUY/SELL, MARKET/LIMIT)
- Position tracking with real-time P&L
- Stop-loss and take-profit automation
- Performance metrics (win rate, Sharpe ratio, max drawdown, profit factor)

### 📱 Android Companion App
- **Dashboard** — Portfolio card, positions, metrics, kill switch
- **Trade Ideas** — AI suggestions with approve/reject workflow
- **Morning Briefing** — Market outlook, events, risk alerts
- **News Feed** — Sentiment-analyzed news with impact badges
- **History** — Performance summary + trade log with P&L
- **Settings** — Connection status, backend URL config

### ⏰ Automated Scheduler
- **8:45 AM IST** — Morning pre-market routine (Mon-Fri)
- **Every 5 min** — Price refresh during market hours (9:15 AM - 3:30 PM)
- **Every 5 min** — Stop-loss / take-profit checks during market hours
- **3:45 PM IST** — Daily metrics snapshot (Mon-Fri)
- **Every 13 min** — Keep-alive ping for Render free tier

---

## Project Structure

```
Trading/
├── backend/
│   ├── ai/                     # AI/ML modules
│   │   ├── news_analyzer.py    # News scraping + sentiment analysis
│   │   ├── decision_engine.py  # Trade idea generation
│   │   ├── morning_routine.py  # Pre-market intelligence
│   │   ├── prompts.py          # Grok AI prompt templates
│   │   └── technical_analysis.py  # RSI, MACD, Bollinger, MAs
│   ├── api/                    # REST API
│   │   ├── routes.py           # 20 endpoints for Android app
│   │   └── auth_middleware.py  # API key authentication
│   ├── data/                   # Database layer
│   │   ├── models.py           # SQLAlchemy + Pydantic models
│   │   ├── database.py         # Async SQLite setup
│   │   └── persistence.py      # Persistence helpers
│   ├── kite/                   # Zerodha broker integration
│   │   ├── auth.py             # OAuth flow + token management
│   │   └── client.py           # Order/position API wrapper
│   ├── mcp_server/             # MCP-compatible tool server
│   │   ├── server.py           # ToolRegistry + GrokToolAgent (9 tools)
│   │   └── tools/
│   │       └── market_tools.py # Yahoo Finance data functions
│   ├── risk/                   # Risk management
│   │   ├── safety_layers.py    # 7-layer safety system
│   │   ├── position_sizer.py   # Kelly Criterion sizing
│   │   ├── kill_switch.py      # Emergency stop
│   │   └── correlation.py      # Sector correlation management
│   ├── trading/                # Trade execution
│   │   ├── paper_trader.py     # Paper trading simulator
│   │   ├── order_manager.py    # Order lifecycle management
│   │   └── portfolio_tracker.py # P&L and performance metrics
│   ├── config.py               # Environment configuration
│   ├── main.py                 # FastAPI application entry point
│   ├── scheduler.py            # APScheduler with 5 automated jobs
│   └── requirements.txt        # Python dependencies
├── android/                    # Android app (Kotlin/Compose)
│   └── app/src/main/java/com/trading/autopilot/
│       ├── data/               # API, models, repository
│       ├── di/                 # Hilt dependency injection
│       ├── ui/                 # Screens + ViewModels (6 screens)
│       ├── TradingApp.kt       # Navigation + bottom bar
│       └── MainActivity.kt     # Entry point
├── tests/                      # Test suite
│   └── backend/
│       ├── test_paper_trader.py    # 12 paper trading tests
│       ├── test_risk_layers.py     # 16 safety layer tests
│       ├── test_order_manager.py   # Order manager tests
│       ├── test_api_routes.py      # API endpoint tests
│       ├── test_config.py          # Configuration tests
│       └── test_mcp_server.py      # MCP tool registry tests
├── docs/
│   └── setup_guide.md
├── logs/
│   └── changelog.md
├── Dockerfile                  # Docker build (Python 3.13 slim)
├── render.yaml                 # Render deployment config
└── pytest.ini                  # Test configuration
```

---

## Quick Start

### Prerequisites
- Python 3.11+ (developed on 3.13)
- Zerodha account with Kite Connect API (optional — for live trading)
- Grok API key from [Groq Console](https://console.groq.com) (for AI features)

### 1. Clone and Setup
```bash
cd d:\Projects\Trading
python -m venv venv
.\venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 2. Configure Environment
```bash
copy backend\.env.example backend\.env
# Edit backend\.env with your API keys
```

### 3. Run the Server
```bash
python -m backend.main
```

### 4. Verify
- **Health**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **MCP Tools**: http://localhost:8000/mcp/tools

### 5. Run Tests
```bash
python -m pytest tests/backend/ -v
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (no auth) |
| `GET` | `/api/dashboard` | Full dashboard data |
| `GET` | `/api/portfolio` | Portfolio summary |
| `GET` | `/api/positions` | Open positions |
| `GET` | `/api/trades` | Trade history |
| `GET` | `/api/metrics` | Performance metrics |
| `POST` | `/api/orders` | Place an order |
| `DELETE` | `/api/orders/{id}` | Cancel an order |
| `POST` | `/api/orders/risk-check` | Pre-trade risk check |
| `GET` | `/api/market/price/{symbol}` | Stock price |
| `GET` | `/api/market/history/{symbol}` | Historical data |
| `GET` | `/api/market/technical/{symbol}` | Technical analysis |
| `GET` | `/api/news` | Analyzed news feed |
| `POST` | `/api/ai/morning-routine` | Run morning routine |
| `GET` | `/api/ai/trade-ideas` | AI trade ideas |
| `GET` | `/api/ai/morning-briefing` | Last morning briefing |
| `POST` | `/api/risk/kill-switch/activate` | Emergency stop |
| `POST` | `/api/risk/kill-switch/deactivate` | Resume trading |
| `GET` | `/api/risk/kill-switch/status` | Kill switch status |
| `GET` | `/api/scheduler/status` | Scheduler & jobs |
| `POST` | `/api/market/refresh-prices` | Manual price refresh |
| `GET` | `/api/kite/login-url` | Kite OAuth login |
| `GET` | `/api/kite/callback` | Kite OAuth callback |
| `GET` | `/api/kite/status` | Kite auth status |
| `GET` | `/mcp/tools` | List MCP tools |
| `POST` | `/mcp/chat` | Chat with AI agent |

All `/api/*` endpoints require the `X-API-Key` header.

---

## API Keys Required

| Service | Get It From | Required? |
|---------|-----------|-----------|
| Groq (Grok AI) | [console.groq.com](https://console.groq.com) | For AI features |
| Kite Connect | [kite.trade](https://kite.trade) | For live/paper trading |

---

## Deployment

The project is configured for deployment on [Render](https://render.com):

```bash
# Build and run via Docker
docker build -t trading-autopilot .
docker run -p 8000:8000 --env-file backend/.env trading-autopilot
```

See `render.yaml` for the full deployment configuration.

---

## License

Private project — not for redistribution.
