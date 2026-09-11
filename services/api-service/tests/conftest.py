"""
Pytest Configuration — API Service
"""

import os
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "postgresql+asyncpg://test_user:test_password@127.0.0.1:5432/test_db"
os.environ["MONGO_URL"] = "mongodb://127.0.0.1:27017/test_db"
os.environ["REDIS_URL"] = "redis://127.0.0.1:6379/0"

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
