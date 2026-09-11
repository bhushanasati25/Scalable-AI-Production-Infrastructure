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

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope="session")
async def setup_test_db():
    import app.models.database  # noqa: F401
    from app.db.postgres import Base, engine

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        yield
