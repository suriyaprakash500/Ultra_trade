"""
Tests for the REST API Routes.

Validates:
- Health check endpoint (no auth)
- Authentication (API key requirement)
- Dashboard, portfolio, positions, metrics endpoints
- Kill switch endpoints
- Kite auth endpoints
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient


# API key from default settings
TEST_API_KEY = "trading_autopilot_dev_key_2026"


@pytest.fixture
def client():
    """Create a test client with mocked dependencies."""
    # Patch the scheduler at its source module
    with patch("backend.scheduler.create_scheduler") as mock_sched:
        mock_scheduler = MagicMock()
        mock_scheduler.running = False
        mock_scheduler.get_jobs.return_value = []
        mock_sched.return_value = mock_scheduler

        # Patch database initialization
        with patch("backend.data.database.init_database", new_callable=AsyncMock):
            with patch("backend.data.database.close_database", new_callable=AsyncMock):
                from backend.main import app
                yield TestClient(app)


def auth_headers():
    """Return valid auth headers."""
    return {"X-API-Key": TEST_API_KEY}


class TestHealthEndpoint:
    """Test the /health endpoint (no auth required)."""

    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_shape(self, client: TestClient):
        response = client.get("/health")
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
        assert "trading_mode" in data
        assert "version" in data
        assert "uptime_seconds" in data

    def test_health_mode_is_paper(self, client: TestClient):
        response = client.get("/health")
        assert response.json()["trading_mode"] == "paper"


class TestRootEndpoint:
    """Test the / root endpoint."""

    def test_root_returns_200(self, client: TestClient):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_response_shape(self, client: TestClient):
        data = client.get("/").json()
        assert "name" in data
        assert data["name"] == "Trading Autopilot"
        assert "version" in data
        assert "docs" in data


class TestAuthentication:
    """Test API key authentication."""

    def test_missing_api_key_returns_403(self, client: TestClient):
        response = client.get("/api/portfolio")
        assert response.status_code == 403

    def test_invalid_api_key_returns_403(self, client: TestClient):
        response = client.get(
            "/api/portfolio",
            headers={"X-API-Key": "wrong_key"},
        )
        assert response.status_code == 403

    def test_valid_api_key_passes(self, client: TestClient):
        response = client.get("/api/portfolio", headers=auth_headers())
        assert response.status_code == 200


class TestDashboardEndpoint:
    """Test the /api/dashboard endpoint."""

    def test_dashboard_returns_200(self, client: TestClient):
        response = client.get("/api/dashboard", headers=auth_headers())
        assert response.status_code == 200

    def test_dashboard_response_shape(self, client: TestClient):
        data = client.get("/api/dashboard", headers=auth_headers()).json()
        assert "portfolio" in data
        assert "positions" in data
        assert "recent_trades" in data
        assert "metrics" in data


class TestPortfolioEndpoints:
    """Test portfolio-related endpoints."""

    def test_portfolio_returns_200(self, client: TestClient):
        response = client.get("/api/portfolio", headers=auth_headers())
        assert response.status_code == 200

    def test_positions_returns_list(self, client: TestClient):
        response = client.get("/api/positions", headers=auth_headers())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_trades_returns_list(self, client: TestClient):
        response = client.get("/api/trades", headers=auth_headers())
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_metrics_returns_200(self, client: TestClient):
        response = client.get("/api/metrics", headers=auth_headers())
        assert response.status_code == 200


class TestKillSwitchEndpoints:
    """Test kill switch endpoints."""

    def test_kill_switch_status(self, client: TestClient):
        response = client.get(
            "/api/risk/kill-switch/status", headers=auth_headers()
        )
        assert response.status_code == 200
        data = response.json()
        assert "active" in data

    def test_kill_switch_activate(self, client: TestClient):
        response = client.post(
            "/api/risk/kill-switch/activate",
            params={"reason": "Test activation"},
            headers=auth_headers(),
        )
        assert response.status_code == 200

    def test_kill_switch_deactivate(self, client: TestClient):
        response = client.post(
            "/api/risk/kill-switch/deactivate",
            headers=auth_headers(),
        )
        assert response.status_code == 200


class TestKiteEndpoints:
    """Test Kite authentication endpoints."""

    def test_login_url_returns_200(self, client: TestClient):
        response = client.get("/api/kite/login-url")
        assert response.status_code == 200
        assert "login_url" in response.json()

    def test_kite_status_returns_200(self, client: TestClient):
        response = client.get("/api/kite/status", headers=auth_headers())
        assert response.status_code == 200
        data = response.json()
        assert "authenticated" in data
        assert "trading_mode" in data


class TestMCPEndpoints:
    """Test MCP tool endpoints."""

    def test_list_tools(self, client: TestClient):
        response = client.get("/mcp/tools")
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        assert "count" in data
        assert data["count"] >= 10  # We have 10 registered tools


class TestSchedulerEndpoint:
    """Test scheduler status endpoint."""

    def test_scheduler_status(self, client: TestClient):
        response = client.get("/api/scheduler/status", headers=auth_headers())
        assert response.status_code == 200
