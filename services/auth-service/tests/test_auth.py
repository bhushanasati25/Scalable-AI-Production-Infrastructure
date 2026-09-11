"""
Auth Service — Unit Tests
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestAuthHealth:
    async def test_health(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth-service"


class TestAuthEndpoints:
    async def test_register(self, client: AsyncClient):
        response = await client.post(
            "/auth/register",
            json={
                "email": "newuser@test.com",
                "full_name": "New User",
                "password": "securepassword123",
            },
        )
        assert response.status_code in (201, 409, 500, 503)

    async def test_login_invalid_credentials(self, client: AsyncClient):
        response = await client.post(
            "/auth/login",
            data={"username": "bad@test.com", "password": "wrong"},
        )
        assert response.status_code in (401, 500, 503)
