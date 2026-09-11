"""
Inference Service — Model Serving Microservice
GPU/CPU-aware model loading with batch inference support.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

import sys

sys.path.insert(0, "/app")
from shared.common.schemas import (
    HealthResponse,
    ServiceName,
    ErrorResponse,
    APIResponse,
    InferenceRequest,
    InferenceResponse,
    TaskStatus,
)
from shared.common.exceptions import BaseServiceError, InferenceError
from shared.common.logging import configure_logging, get_logger


# ── Settings ──
class InferenceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "inference-service"
    environment: str = "development"
    log_level: str = "INFO"
    inference_port: int = 8002
    version: str = "0.1.0"

    device: str = "cpu"
    max_batch_size: int = 32
    model_path: str = "/app/models"
    inference_timeout: int = 60
    redis_url: str = "redis://redis:6379/0"


settings = InferenceSettings()

# ── Model Registry ──
_loaded_models: dict[str, dict[str, Any]] = {}
_start_time: float = 0.0


def load_model(model_name: str) -> dict[str, Any]:
    """
    Load a model into memory.
    TODO: Replace with actual model loading (PyTorch, TensorFlow, ONNX).
    """
    logger = get_logger(__name__)
    logger.info("Loading model", model=model_name, device=settings.device)

    # Simulated model metadata
    model_info = {
        "name": model_name,
        "version": "1.0.0",
        "device": settings.device,
        "loaded_at": time.time(),
        "status": "loaded",
    }

    _loaded_models[model_name] = model_info
    logger.info("Model loaded", model=model_name)
    return model_info


# Pre-load default models
load_model("text-classifier-v1")
load_model("sentiment-analyzer-v2")


def run_model_inference(model_name: str, input_data: dict, params: dict) -> dict:
    """
    Run inference on a loaded model.
    TODO: Replace with actual model inference.
    """
    if model_name not in _loaded_models:
        raise InferenceError(f"Model '{model_name}' is not loaded", model=model_name)

    # Simulated inference
    start = time.time()
    if settings.environment != "testing":
        time.sleep(0.01)  # Simulate model compute

    result = {
        "predictions": [
            {"label": "positive", "score": 0.92},
            {"label": "neutral", "score": 0.06},
            {"label": "negative", "score": 0.02},
        ],
        "model_version": _loaded_models[model_name]["version"],
        "device": settings.device,
    }

    latency_ms = (time.time() - start) * 1000
    return {"output": result, "latency_ms": round(latency_ms, 2)}


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _start_time

    configure_logging(
        settings.service_name, settings.log_level, json_format=settings.environment != "development"
    )
    logger = get_logger(__name__)
    logger.info("Starting Inference Service", version=settings.version, device=settings.device)
    _start_time = time.time()

    # Pre-load default models
    if "text-classifier-v1" not in _loaded_models:
        load_model("text-classifier-v1")
    if "sentiment-analyzer-v2" not in _loaded_models:
        load_model("sentiment-analyzer-v2")

    logger.info("Inference Service ready", models_loaded=len(_loaded_models))

    yield

    logger.info("Inference Service stopping")


# ── App ──
app = FastAPI(
    title="Inference Service",
    description="Model Serving with GPU/CPU Support",
    version=settings.version,
    lifespan=lifespan,
)


@app.exception_handler(BaseServiceError)
async def service_error_handler(request: Request, exc: BaseServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(error=exc.error_code, detail=exc.message).model_dump(mode="json"),
    )


# ── Health ──
@app.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        service=ServiceName.INFERENCE,
        version=settings.version,
        uptime_seconds=round(time.time() - _start_time, 2),
        checks={
            "device": settings.device,
            "models_loaded": str(len(_loaded_models)),
        },
    )


# ── Inference Endpoints ──
@app.post("/inference/predict", response_model=APIResponse[InferenceResponse])
async def predict(request: InferenceRequest) -> APIResponse[InferenceResponse]:
    """Run synchronous inference on a loaded model."""
    logger = get_logger(__name__)
    import uuid

    request_id = str(uuid.uuid4())
    logger.info("Inference request", request_id=request_id, model=request.model_name)

    try:
        result = run_model_inference(
            model_name=request.model_name,
            input_data=request.input_data,
            params=request.parameters,
        )

        return APIResponse(
            data=InferenceResponse(
                request_id=request_id,
                model_name=request.model_name,
                status=TaskStatus.COMPLETED,
                output=result["output"],
                latency_ms=result["latency_ms"],
            ),
        )

    except InferenceError:
        raise
    except Exception as exc:
        logger.error("Inference failed", request_id=request_id, error=str(exc))
        raise InferenceError(str(exc), model=request.model_name)


class BatchRequest(BaseModel):
    model_name: str
    inputs: list[dict[str, Any]]
    parameters: dict[str, Any] = Field(default_factory=dict)


class BatchResponse(BaseModel):
    results: list[dict[str, Any]]
    total_latency_ms: float
    batch_size: int


@app.post("/inference/batch", response_model=APIResponse[BatchResponse])
async def batch_predict(request: BatchRequest) -> APIResponse[BatchResponse]:
    """Run batch inference on multiple inputs."""
    logger = get_logger(__name__)

    if len(request.inputs) > settings.max_batch_size:
        from shared.common.exceptions import BadRequestError

        raise BadRequestError(
            f"Batch size {len(request.inputs)} exceeds maximum {settings.max_batch_size}"
        )

    start = time.time()
    results = []

    for input_data in request.inputs:
        result = run_model_inference(
            model_name=request.model_name,
            input_data=input_data,
            params=request.parameters,
        )
        results.append(result["output"])

    total_latency = (time.time() - start) * 1000

    logger.info(
        "Batch inference completed",
        model=request.model_name,
        batch_size=len(request.inputs),
        total_latency_ms=round(total_latency, 2),
    )

    return APIResponse(
        data=BatchResponse(
            results=results,
            total_latency_ms=round(total_latency, 2),
            batch_size=len(request.inputs),
        ),
    )


@app.get("/inference/models")
async def list_loaded_models() -> APIResponse[list[dict]]:
    """List all currently loaded models."""
    models = [
        {
            "name": name,
            "version": info["version"],
            "device": info["device"],
            "status": info["status"],
        }
        for name, info in _loaded_models.items()
    ]
    return APIResponse(data=models)


@app.post("/inference/models/{model_name}/load")
async def load_model_endpoint(model_name: str) -> APIResponse[dict]:
    """Load a model into memory."""
    if model_name in _loaded_models:
        return APIResponse(data=_loaded_models[model_name], message="Model already loaded")

    model_info = load_model(model_name)
    return APIResponse(data=model_info, message="Model loaded successfully")
