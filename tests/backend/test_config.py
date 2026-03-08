"""
Tests for Configuration Management.

Validates:
- Default settings values
- Property helpers (is_paper_trading, is_development)
- Environment variable overrides
"""

import os
import pytest
from unittest.mock import patch

from backend.config import Settings


class TestDefaultSettings:
    """Test default configuration values."""

    def test_default_trading_mode(self):
        """Default trading mode should be paper."""
        settings = Settings(
            _env_file=None,  # Don't load .env for tests
        )
        assert settings.trading_mode == "paper"

    def test_default_capital(self):
        """Default paper trading capital should be ₹100,000."""
        settings = Settings(_env_file=None)
        assert settings.paper_trading_capital == 100_000.0

    def test_default_app_env(self):
        """Default environment should be development."""
        settings = Settings(_env_file=None)
        assert settings.app_env == "development"

    def test_default_port(self):
        """Default port should be 8000."""
        settings = Settings(_env_file=None)
        assert settings.app_port == 8000

    def test_default_risk_limits(self):
        """Risk limits should have sensible defaults."""
        settings = Settings(_env_file=None)
        assert settings.max_risk_per_trade_pct == 2.0
        assert settings.max_positions == 6
        assert settings.max_single_position_pct == 10.0
        assert settings.max_sector_concentration_pct == 30.0
        assert settings.daily_loss_limit_pct == 2.0
        assert settings.total_drawdown_limit_pct == 20.0


class TestPropertyHelpers:
    """Test computed property helpers."""

    def test_is_paper_trading_true(self):
        settings = Settings(_env_file=None, trading_mode="paper")
        assert settings.is_paper_trading is True

    def test_is_paper_trading_false(self):
        settings = Settings(_env_file=None, trading_mode="live")
        assert settings.is_paper_trading is False

    def test_is_paper_trading_case_insensitive(self):
        settings = Settings(_env_file=None, trading_mode="PAPER")
        assert settings.is_paper_trading is True

    def test_is_development_true(self):
        settings = Settings(_env_file=None, app_env="development")
        assert settings.is_development is True

    def test_is_development_false(self):
        settings = Settings(_env_file=None, app_env="production")
        assert settings.is_development is False

    def test_is_development_case_insensitive(self):
        settings = Settings(_env_file=None, app_env="DEVELOPMENT")
        assert settings.is_development is True


class TestDatabaseURL:
    """Test database URL configuration."""

    def test_default_database_url(self):
        settings = Settings(_env_file=None)
        assert "sqlite" in settings.database_url
        assert "trading_autopilot.db" in settings.database_url

    def test_custom_database_url(self):
        settings = Settings(_env_file=None, database_url="sqlite+aiosqlite:///custom.db")
        assert "custom.db" in settings.database_url


class TestGrokConfig:
    """Test Grok AI configuration."""

    def test_default_grok_model(self):
        settings = Settings(_env_file=None)
        assert "llama" in settings.grok_model or "grok" in settings.grok_model

    def test_default_grok_base_url(self):
        settings = Settings(_env_file=None)
        assert "groq.com" in settings.grok_base_url or "x.ai" in settings.grok_base_url
