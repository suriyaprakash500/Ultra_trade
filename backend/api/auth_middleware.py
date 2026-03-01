"""
Trading Autopilot — API Authentication Middleware.

Simple API key authentication for securing the REST endpoints.
The Android app sends the key in the `X-API-Key` header.
"""

from __future__ import annotations

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from starlette.status import HTTP_403_FORBIDDEN

from backend.config import get_settings

# Header name the Android app will use
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(
    api_key: str | None = Security(_api_key_header),
) -> str:
    """
    FastAPI dependency that validates the API key.

    Usage in route::

        @router.get("/protected")
        async def protected_route(key: str = Depends(require_api_key)):
            ...

    Raises:
        HTTPException 403 if the key is missing or invalid.
    """
    settings = get_settings()
    expected_key = settings.app_secret_key

    if not api_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Missing API key. Include X-API-Key header.",
        )

    if api_key != expected_key:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
