"""
Inference Service — Unit Tests
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


class TestInferenceHealth:
    async def test_health(self, client: AsyncClient):
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "inference-service"
        assert "models_loaded" in data.get("checks", {})


class TestInferencePredict:
    async def test_predict_valid_model(self, client: AsyncClient):
        response = await client.post(
            "/inference/predict",
            json={
                "model_name": "text-classifier-v1",
                "input_data": {"text": "hello world"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["status"] == "completed"
        assert data["data"]["latency_ms"] is not None

    async def test_predict_invalid_model(self, client: AsyncClient):
        response = await client.post(
            "/inference/predict",
            json={
                "model_name": "nonexistent-model",
                "input_data": {"text": "hello"},
            },
        )
        assert response.status_code == 500


class TestBatchInference:
    async def test_batch_predict(self, client: AsyncClient):
        response = await client.post(
            "/inference/batch",
            json={
                "model_name": "text-classifier-v1",
                "inputs": [
                    {"text": "hello"},
                    {"text": "world"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["data"]["batch_size"] == 2

    async def test_batch_exceeds_max(self, client: AsyncClient):
        inputs = [{"text": f"item_{i}"} for i in range(100)]
        response = await client.post(
            "/inference/batch",
            json={
                "model_name": "text-classifier-v1",
                "inputs": inputs,
            },
        )
        assert response.status_code == 400


class TestModelManagement:
    async def test_list_models(self, client: AsyncClient):
        response = await client.get("/inference/models")
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 2

    async def test_load_model(self, client: AsyncClient):
        response = await client.post("/inference/models/new-model/load")
        assert response.status_code == 200
