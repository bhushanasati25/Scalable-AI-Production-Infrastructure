"""
Pytest Configuration — API Service
"""

import os

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test_user:test_password@127.0.0.1:5432/test_db"
)
os.environ.setdefault("MONGO_URL", "mongodb://127.0.0.1:27017/test_db")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")

import contextlib

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope="session")
def setup_test_db():
    import asyncio

    import app.models.database  # noqa: F401
    from app.db.postgres import Base, engine

    async def _setup():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pass

    async def _teardown():
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
            await engine.dispose()
        except Exception:
            pass

    with contextlib.suppress(Exception):
        asyncio.run(_setup())

    yield

    with contextlib.suppress(Exception):
        asyncio.run(_teardown())
