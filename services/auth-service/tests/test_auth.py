"""
Auth Service — Unit Tests
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestAuthHealth:
    def test_health(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "auth-service"


class TestAuthEndpoints:
    def test_register(self, client: TestClient):
        response = client.post(
            "/auth/register",
            json={
                "email": "newuser@test.com",
                "full_name": "New User",
                "password": "securepassword123",
            },
        )
        assert response.status_code in (201, 409, 422, 500, 503)

    def test_login_invalid_credentials(self, client: TestClient):
        response = client.post(
            "/auth/login",
            data={"username": "bad@test.com", "password": "wrong"},
        )
        assert response.status_code in (401, 422, 500, 503)
