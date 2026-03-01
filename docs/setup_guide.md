# Trading Autopilot — Setup Guide

## Prerequisites
- Python 3.11+
- Zerodha account with Kite Connect Personal API
- Grok (xAI) API key

## Quick Start

### 1. Clone and setup
```bash
cd d:\Projects\Trading
python -m venv venv
.\venv\Scripts\activate
pip install -r backend\requirements.txt
```

### 2. Configure environment
```bash
copy backend\.env.example backend\.env
# Edit backend\.env with your keys
```

### 3. Run the server
```bash
python -m backend.main
```

### 4. Verify
- Health: http://localhost:8000/health
- API Docs: http://localhost:8000/docs
- MCP: http://localhost:8000/mcp

### 5. Run tests
```bash
python -m pytest tests/backend/ -v
```

## API Keys Required
| Service | Get It From | Required? |
|---------|------------|-----------|
| Kite Connect | https://kite.trade | For live/paper trading |
| Grok (xAI) | https://console.x.ai | For AI features |
