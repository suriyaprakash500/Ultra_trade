"""
Trading Autopilot — Configuration Management.

Centralized settings loaded from environment variables with validation.
All settings are immutable at runtime and accessed via the `get_settings()` singleton.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Resolve .env relative to this file (backend/.env)
_ENV_FILE = Path(__file__).resolve().parent / ".env"


class Settings(BaseSettings):
    """Application settings loaded from .env file and environment variables."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Kite Connect (Zerodha) ──────────────────────────────────────
    kite_api_key: str = ""
    kite_api_secret: str = ""
    kite_redirect_url: str = "http://localhost:8000/api/kite/callback"

    # ── Grok AI (xAI) ──────────────────────────────────────────────
    grok_api_key: str = ""
    grok_model: str = "grok-3-mini-fast"
    grok_base_url: str = "https://api.x.ai/v1"

    # ── App Settings ───────────────────────────────────────────────
    app_secret_key: str = "trading_autopilot_dev_key_2026"
    app_env: str = "development"
    app_port: int = 8000
    app_host: str = "0.0.0.0"

    # ── Trading Settings ───────────────────────────────────────────
    trading_mode: str = "paper"  # "paper" or "live"
    paper_trading_capital: float = 100_000.0
    max_risk_per_trade_pct: float = 2.0
    max_positions: int = 6
    max_single_position_pct: float = 10.0
    max_sector_concentration_pct: float = 30.0
    max_portfolio_beta: float = 1.3
    daily_loss_limit_pct: float = 2.0
    weekly_loss_limit_pct: float = 5.0
    monthly_loss_limit_pct: float = 10.0
    total_drawdown_limit_pct: float = 20.0

    # ── Database ───────────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./trading_autopilot.db"

    @property
    def is_paper_trading(self) -> bool:
        """Check if system is in paper trading mode."""
        return self.trading_mode.lower() == "paper"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """
    Return a cached Settings singleton.

    Uses `lru_cache` so the .env file is read only once per process lifetime.
    """
    return Settings()
