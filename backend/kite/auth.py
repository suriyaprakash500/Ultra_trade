"""
Trading Autopilot — Kite Connect Authentication.

Handles the OAuth login flow for Zerodha Kite Connect:
1. Generate a login URL for the user to authenticate in a WebView.
2. Receive the redirect with request_token.
3. Exchange request_token for access_token (secure, server-side).
4. Persist and refresh the access_token (valid ~24 hours).

Uses httpx for direct API calls instead of the kiteconnect SDK.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from typing import Optional

import httpx
from loguru import logger

from backend.config import get_settings

# Kite Connect API base URL
KITE_API_BASE = "https://api.kite.trade"


class KiteAuth:
    """
    Manages Kite Connect authentication lifecycle.

    The access_token is stored in-memory and refreshed daily.
    For production, persist it in the database or a secure store.
    """

    def __init__(self) -> None:
        settings = get_settings()
        self._api_key: str = settings.kite_api_key
        self._api_secret: str = settings.kite_api_secret
        self._redirect_url: str = settings.kite_redirect_url

        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._request_token: Optional[str] = None

    # ── Properties ─────────────────────────────────────────────────

    @property
    def is_authenticated(self) -> bool:
        """True if we have a valid, non-expired access token."""
        if not self._access_token or not self._token_expiry:
            return False
        return datetime.utcnow() < self._token_expiry

    @property
    def access_token(self) -> Optional[str]:
        """Return the current access token, or None if expired."""
        if self.is_authenticated:
            return self._access_token
        return None

    @property
    def login_url(self) -> str:
        """URL the user must visit to authenticate with Zerodha."""
        return (
            f"https://kite.zerodha.com/connect/login"
            f"?v=3&api_key={self._api_key}"
        )

    # ── Core Methods ───────────────────────────────────────────────

    def generate_checksum(self, request_token: str) -> str:
        """
        Generate the SHA-256 checksum required for token exchange.

        checksum = SHA256(api_key + request_token + api_secret)
        """
        raw = self._api_key + request_token + self._api_secret
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    async def exchange_token(self, request_token: str) -> str:
        """
        Exchange a request_token for an access_token via Kite API.

        POST /session/token with api_key, request_token, and checksum.

        Returns:
            The access_token string.
        """
        if not self._api_key or not self._api_secret:
            raise ValueError(
                "Kite API key and secret must be configured in .env"
            )

        self._request_token = request_token
        checksum = self.generate_checksum(request_token)

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{KITE_API_BASE}/session/token",
                    data={
                        "api_key": self._api_key,
                        "request_token": request_token,
                        "checksum": checksum,
                    },
                )
                response.raise_for_status()
                data = response.json()

            if data.get("status") == "success":
                self._access_token = data["data"]["access_token"]
                # Kite tokens expire at ~6 AM IST next day
                self._token_expiry = datetime.utcnow() + timedelta(hours=20)

                logger.info(
                    "Kite authentication successful, "
                    f"token expires at {self._token_expiry.isoformat()}"
                )
                return self._access_token
            else:
                raise RuntimeError(f"Kite auth failed: {data.get('message', 'Unknown error')}")

        except httpx.HTTPStatusError as exc:
            logger.error(f"Kite token exchange HTTP error: {exc.response.text}")
            raise RuntimeError(f"Kite token exchange failed: {exc}") from exc
        except Exception as exc:
            logger.error(f"Kite token exchange failed: {exc}")
            raise RuntimeError(f"Kite token exchange failed: {exc}") from exc

    def set_access_token(self, token: str) -> None:
        """
        Manually set an access token (e.g., loaded from persistent storage).

        Useful for resuming a session without re-authenticating.
        """
        self._access_token = token
        self._token_expiry = datetime.utcnow() + timedelta(hours=20)
        logger.info("Access token set manually")

    def invalidate(self) -> None:
        """Clear the current session (force re-login)."""
        self._access_token = None
        self._token_expiry = None
        self._request_token = None
        logger.info("Kite session invalidated")


# ── Module-level singleton ─────────────────────────────────────────

_kite_auth = KiteAuth()


def get_kite_auth() -> KiteAuth:
    """Return the global KiteAuth singleton."""
    return _kite_auth
