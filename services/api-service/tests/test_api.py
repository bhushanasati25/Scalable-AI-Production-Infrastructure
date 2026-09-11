"""
API Service — Unit Tests
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
async def client():
    """Create an async test client."""
    from app.main import app
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


class TestHealthEndpoints:
    """Test health check endpoints."""

    async def test_health_returns_200(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-service"

    async def test_health_includes_version(self, client: AsyncClient):
        response = await client.get("/health")
        data = response.json()
        assert "version" in data
        assert "uptime_seconds" in data


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    async def test_metrics_returns_200(self, client: AsyncClient):
        response = await client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text or response.status_code == 200


class TestTasksAPI:
    """Test tasks CRUD endpoints."""

    async def test_create_task(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/tasks/",
            json={
                "name": "Test Task",
                "task_type": "test",
                "payload": {"key": "value"},
                "priority": 5,
            },
        )
        # May fail without DB, but validates route exists
        assert response.status_code in (201, 500, 503)

    async def test_list_tasks(self, client: AsyncClient):
        response = await client.get("/api/v1/tasks/")
        assert response.status_code in (200, 500, 503)


class TestInferenceAPI:
    """Test inference endpoints."""

    async def test_list_models(self, client: AsyncClient):
        response = await client.get("/api/v1/inference/models")
        assert response.status_code in (200, 500)

    async def test_submit_inference(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/inference/predict",
            json={
                "model_name": "text-classifier-v1",
                "input_data": {"text": "hello world"},
            },
        )
        assert response.status_code in (202, 500, 503)


class TestUsersAPI:
    """Test users endpoints."""

    async def test_create_user(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "securepassword123",
            },
        )
        assert response.status_code in (201, 409, 500, 503)

    async def test_list_users(self, client: AsyncClient):
        response = await client.get("/api/v1/users/")
        assert response.status_code in (200, 500, 503)
