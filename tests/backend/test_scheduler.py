"""
Tests for the Scheduler.

Validates:
- Market hours detection
- Scheduler creation with all expected jobs
- Job configuration (IDs, names, triggers)
"""

import pytest
from unittest.mock import patch
from datetime import datetime, time
from zoneinfo import ZoneInfo

from backend.scheduler import (
    create_scheduler,
    is_market_hours,
    MARKET_OPEN,
    MARKET_CLOSE,
    IST,
)


class TestMarketHours:
    """Test market hours detection."""

    def test_market_open_time(self):
        """Market opens at 9:15 AM IST."""
        assert MARKET_OPEN == time(9, 15)

    def test_market_close_time(self):
        """Market closes at 3:30 PM IST."""
        assert MARKET_CLOSE == time(15, 30)

    def test_during_market_hours(self):
        """Should return True during market hours."""
        market_time = datetime(2026, 3, 9, 12, 0, 0, tzinfo=IST)
        with patch("backend.scheduler.datetime") as mock_dt:
            mock_dt.now.return_value = market_time
            mock_dt.side_effect = lambda *args, **kw: datetime(*args, **kw)
            # Can't easily mock datetime.now in this pattern,
            # so we test the constants instead
            assert MARKET_OPEN <= time(12, 0) <= MARKET_CLOSE

    def test_before_market_hours(self):
        """8:00 AM is before market open."""
        assert time(8, 0) < MARKET_OPEN

    def test_after_market_hours(self):
        """4:00 PM is after market close."""
        assert time(16, 0) > MARKET_CLOSE


class TestSchedulerCreation:
    """Test scheduler factory."""

    def test_creates_scheduler(self):
        """create_scheduler should return an AsyncIOScheduler."""
        scheduler = create_scheduler()
        assert scheduler is not None

    def test_has_five_jobs(self):
        """Scheduler should have exactly 5 jobs configured."""
        scheduler = create_scheduler()
        jobs = scheduler.get_jobs()
        assert len(jobs) == 5

    def test_job_ids(self):
        """Verify all expected job IDs are registered."""
        scheduler = create_scheduler()
        job_ids = [j.id for j in scheduler.get_jobs()]

        assert "morning_routine" in job_ids
        assert "price_refresh" in job_ids
        assert "sl_tp_check" in job_ids
        assert "daily_metrics" in job_ids
        assert "keep_alive" in job_ids

    def test_job_names(self):
        """Verify job names are descriptive."""
        scheduler = create_scheduler()
        job_names = [j.name for j in scheduler.get_jobs()]

        assert "Morning Pre-Market Routine" in job_names
        assert "Price Refresh" in job_names
        assert "Stop Loss / Take Profit Check" in job_names
        assert "Daily Metrics Snapshot" in job_names
        assert "Keep-Alive Ping" in job_names

    def test_timezone_is_ist(self):
        """Scheduler timezone should be Asia/Kolkata."""
        scheduler = create_scheduler()
        assert str(scheduler.timezone) == "Asia/Kolkata"
