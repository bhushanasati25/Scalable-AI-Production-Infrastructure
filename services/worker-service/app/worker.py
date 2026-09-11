"""
Worker Service — Celery Async Task Workers
Handles background processing, inference dispatching, and data pipeline tasks.
"""

from __future__ import annotations

import sys
import time
from datetime import UTC, datetime

from celery import Celery, Task
from celery.signals import worker_init, worker_shutdown
from pydantic_settings import BaseSettings, SettingsConfigDict

sys.path.insert(0, "/app")
from shared.common.logging import configure_logging, get_logger


# ── Settings ──
class WorkerSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    service_name: str = "worker-service"
    environment: str = "development"
    log_level: str = "INFO"

    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"
    celery_concurrency: int = 4
    celery_task_timeout: int = 300

    database_url: str = "postgresql+asyncpg://app_user:password@postgres:5432/scalable_ai"
    mongo_url: str = (
        "mongodb://app_user:password@mongo:27017/scalable_ai_docs?authSource=scalable_ai_docs"
    )


settings = WorkerSettings()

# ── Celery App ──
celery_app = Celery(
    "scalable_ai_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Reliability
    task_acks_late=True,  # Acknowledge after completion
    worker_prefetch_multiplier=1,  # Fair distribution
    task_reject_on_worker_lost=True,
    task_soft_time_limit=settings.celery_task_timeout - 30,
    task_time_limit=settings.celery_task_timeout,
    # Retry
    task_default_retry_delay=60,
    task_max_retries=3,
    # Queues
    task_default_queue="default",
    task_routes={
        "app.worker.tasks.run_inference": {"queue": "inference"},
        "app.worker.tasks.process_data_pipeline": {"queue": "data-pipeline"},
    },
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Concurrency
    worker_concurrency=settings.celery_concurrency,
)


# ── Signals ──
@worker_init.connect
def on_worker_init(**kwargs):
    configure_logging(
        settings.service_name, settings.log_level, json_format=settings.environment != "development"
    )
    logger = get_logger(__name__)
    logger.info("Celery worker initialized", concurrency=settings.celery_concurrency)


@worker_shutdown.connect
def on_worker_shutdown(**kwargs):
    logger = get_logger(__name__)
    logger.info("Celery worker shutting down")


# ── Base Task with Retry ──
class RetryTask(Task):
    """Base task class with automatic retry on failure."""

    autoretry_for = (Exception,)
    retry_kwargs = {"max_retries": 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


# ── Tasks ──
@celery_app.task(bind=True, base=RetryTask, name="app.worker.tasks.run_inference")
def run_inference(
    self, request_id: str, model_name: str, input_data: dict, params: dict | None = None
):
    """
    Execute model inference as a background task.
    Updates both PostgreSQL (status) and MongoDB (logs).
    """
    logger = get_logger(__name__)
    logger.info("Starting inference task", request_id=request_id, model=model_name)

    start_time = time.time()

    try:
        # Simulate inference processing
        # TODO: Forward to inference-service via HTTP or gRPC
        import time as t

        t.sleep(2)  # Simulate model inference latency

        result = {
            "predictions": [0.85, 0.12, 0.03],
            "labels": ["positive", "neutral", "negative"],
            "model_version": "1.0.0",
        }

        latency_ms = (time.time() - start_time) * 1000

        logger.info(
            "Inference completed",
            request_id=request_id,
            model=model_name,
            latency_ms=round(latency_ms, 2),
        )

        return {
            "request_id": request_id,
            "status": "completed",
            "result": result,
            "latency_ms": round(latency_ms, 2),
        }

    except Exception as exc:
        logger.error(
            "Inference failed",
            request_id=request_id,
            model=model_name,
            error=str(exc),
        )
        raise


@celery_app.task(bind=True, base=RetryTask, name="app.worker.tasks.process_data_pipeline")
def process_data_pipeline(self, pipeline_id: str, config: dict):
    """Process a data pipeline task."""
    logger = get_logger(__name__)
    logger.info("Processing data pipeline", pipeline_id=pipeline_id)

    # Simulate data processing
    time.sleep(1)

    return {
        "pipeline_id": pipeline_id,
        "status": "completed",
        "records_processed": 1000,
        "completed_at": datetime.now(UTC).isoformat(),
    }


@celery_app.task(name="app.worker.tasks.health_check")
def health_check():
    """Simple task for health checking the worker."""
    return {"status": "healthy", "timestamp": datetime.now(UTC).isoformat()}
