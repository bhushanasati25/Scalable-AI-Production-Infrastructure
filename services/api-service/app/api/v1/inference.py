"""
Inference API — Endpoints for model inference requests.
"""

from __future__ import annotations

import time
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.postgres import get_db_session
from app.db.mongodb import get_inference_logs_collection
from app.models.database import InferenceJob

import sys
sys.path.insert(0, "/app")
from shared.common.schemas import (
    APIResponse,
    InferenceRequest,
    InferenceResponse,
    TaskStatus,
)
from shared.common.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/predict",
    response_model=APIResponse[InferenceResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def submit_inference(
    request: InferenceRequest,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[InferenceResponse]:
    """Submit an inference request for processing."""
    request_id = str(uuid.uuid4())
    # TODO: get owner_id from auth token
    owner_id = uuid.uuid4()

    # Create tracking record in PostgreSQL
    job = InferenceJob(
        request_id=request_id,
        model_name=request.model_name,
        status="pending",
        input_params=request.input_data,
        owner_id=owner_id,
    )
    db.add(job)
    await db.flush()

    # Log to MongoDB for analytics
    inference_logs = get_inference_logs_collection()
    await inference_logs.insert_one({
        "request_id": request_id,
        "model_name": request.model_name,
        "status": "pending",
        "input_data": request.input_data,
        "parameters": request.parameters,
        "created_at": datetime.utcnow(),
        "metadata": {
            "timeout": request.timeout,
        },
    })

    # TODO: dispatch to Celery worker for actual inference
    logger.info(
        "Inference request submitted",
        request_id=request_id,
        model=request.model_name,
    )

    return APIResponse(
        data=InferenceResponse(
            request_id=request_id,
            model_name=request.model_name,
            status=TaskStatus.PENDING,
            metadata={"queued": True},
        ),
        message="Inference request queued for processing",
    )


@router.get(
    "/status/{request_id}",
    response_model=APIResponse[InferenceResponse],
)
async def get_inference_status(
    request_id: str,
    db: AsyncSession = Depends(get_db_session),
) -> APIResponse[InferenceResponse]:
    """Check the status of an inference request."""
    from sqlalchemy import select

    result = await db.execute(
        select(InferenceJob).where(InferenceJob.request_id == request_id)
    )
    job = result.scalar_one_or_none()

    if not job:
        from shared.common.exceptions import NotFoundError
        raise NotFoundError("InferenceJob", request_id)

    return APIResponse(
        data=InferenceResponse(
            request_id=job.request_id,
            model_name=job.model_name,
            status=TaskStatus(job.status),
            output=job.output_data,
            latency_ms=job.latency_ms,
        ),
    )


@router.get("/models")
async def list_models() -> APIResponse[list[dict]]:
    """List available models for inference."""
    # TODO: Dynamically discover loaded models from inference service
    models = [
        {
            "name": "text-classifier-v1",
            "version": "1.0.0",
            "status": "loaded",
            "device": "cpu",
            "max_batch_size": 32,
        },
        {
            "name": "sentiment-analyzer-v2",
            "version": "2.1.0",
            "status": "loaded",
            "device": "cpu",
            "max_batch_size": 64,
        },
    ]
    return APIResponse(data=models)
