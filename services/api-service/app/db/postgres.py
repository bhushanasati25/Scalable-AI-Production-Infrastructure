"""
PostgreSQL async database connection with SQLAlchemy 2.0.
Production-grade connection pooling and session management.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

import sys
from app.core.config import get_settings

settings = get_settings()

# ── Engine ──
connect_args = {"timeout": 1} if ("pytest" in sys.modules or settings.is_testing) else {}
engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=settings.db_pool_recycle,
    pool_timeout=1 if ("pytest" in sys.modules or settings.is_testing) else settings.db_pool_timeout,
    pool_pre_ping=True,  # Verify connections before use
    echo=settings.db_echo,
    connect_args=connect_args,
)


# ── Session Factory ──
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ──
class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy models."""
    pass


# ── Session Dependency ──
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency: yields a database session with auto-rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database sessions outside of FastAPI routes."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Lifecycle ──
async def init_db() -> None:
    """Initialize database: create tables (dev only) and verify connection."""
    async with engine.begin() as conn:
        # Verify connectivity
        await conn.execute(text("SELECT 1"))

        # In development, auto-create tables
        if settings.is_development:
            await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Dispose of the engine and close all connections."""
    await engine.dispose()


async def check_db_health() -> bool:
    """Check PostgreSQL connectivity for health endpoints."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
