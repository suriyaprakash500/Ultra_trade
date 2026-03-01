"""
Trading Autopilot — Database Setup.

Provides async SQLAlchemy engine, session factory, and table initialization.
Uses SQLite for development (easily swappable to PostgreSQL for production).
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from loguru import logger
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.config import get_settings
from backend.data.models import Base

# ── Engine & Session Factory ───────────────────────────────────────

_engine = create_async_engine(
    get_settings().database_url,
    echo=get_settings().is_development,
    pool_pre_ping=True,
)

_session_factory = async_sessionmaker(
    bind=_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Public API ─────────────────────────────────────────────────────

async def init_database() -> None:
    """Create all tables if they don't exist."""
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables initialized successfully")


async def close_database() -> None:
    """Dispose of the database engine."""
    await _engine.dispose()
    logger.info("Database connection closed")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Yield an async database session with automatic commit/rollback.

    Usage::

        async with get_session() as session:
            session.add(some_record)
            # auto-commits on exit, rolls back on exception
    """
    session = _session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
