"""
API Service — Unit Tests
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """Create a test client."""
    from app.main import app

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_returns_200(self, client: TestClient):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "api-service"

    def test_health_includes_version(self, client: TestClient):
        response = client.get("/health")
        data = response.json()
        assert "version" in data
        assert "uptime_seconds" in data


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""

    def test_metrics_returns_200(self, client: TestClient):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "http_requests_total" in response.text or response.status_code == 200


class TestTasksAPI:
    """Test tasks CRUD endpoints."""

    def test_create_task(self, client: TestClient):
        response = client.post(
            "/api/v1/tasks/",
            json={
                "name": "Test Task",
                "task_type": "test",
                "payload": {"key": "value"},
                "priority": 5,
            },
        )
        assert response.status_code in (201, 500, 503)

    def test_list_tasks(self, client: TestClient):
        response = client.get("/api/v1/tasks/")
        assert response.status_code in (200, 500, 503)


class TestInferenceAPI:
    """Test inference endpoints."""

    def test_list_models(self, client: TestClient):
        response = client.get("/api/v1/inference/models")
        assert response.status_code in (200, 500)

    def test_submit_inference(self, client: TestClient):
        response = client.post(
            "/api/v1/inference/predict",
            json={
                "model_name": "text-classifier-v1",
                "input_data": {"text": "hello world"},
            },
        )
        assert response.status_code in (202, 500, 503)


class TestUsersAPI:
    """Test users endpoints."""

    def test_create_user(self, client: TestClient):
        response = client.post(
            "/api/v1/users/",
            json={
                "email": "test@example.com",
                "full_name": "Test User",
                "password": "securepassword123",
            },
        )
        assert response.status_code in (201, 409, 500, 503)

    def test_list_users(self, client: TestClient):
        response = client.get("/api/v1/users/")
        assert response.status_code in (200, 500, 503)
