"""
Pytest Configuration — Auth Service
"""

import os

os.environ.setdefault(
    "DATABASE_URL", "postgresql+asyncpg://test_user:test_password@127.0.0.1:5432/test_db"
)
os.environ.setdefault("ENVIRONMENT", "testing")

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(autouse=True, scope="session")
async def setup_test_db():
    from app.main import engine
    from app.models import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        yield
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    except Exception:
        yield
