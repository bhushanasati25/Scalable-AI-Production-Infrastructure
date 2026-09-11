"""
Pytest Configuration — Auth Service
"""

import os
os.environ["DATABASE_URL"] = "postgresql+asyncpg://app_user:password@127.0.0.1:5432/scalable_ai"
os.environ["ENVIRONMENT"] = "testing"

import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
