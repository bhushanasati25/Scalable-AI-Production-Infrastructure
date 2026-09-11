"""
API Service — FastAPI Application Entry Point
Production-grade with lifespan management, error handling, and middleware.
"""

from __future__ import annotations

# Shared library imports
import sys
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from app.api.v1 import router as v1_router
from app.core.config import get_settings
from app.db.mongodb import check_mongo_health, close_mongo, init_mongo
from app.db.postgres import check_db_health, close_db, init_db
from app.db.redis import check_redis_health, close_redis, init_redis

sys.path.insert(0, "/app")
from shared.common.exceptions import BaseServiceError
from shared.common.logging import configure_logging, get_logger, set_correlation_id
from shared.common.schemas import ErrorResponse, HealthResponse, ServiceName

settings = get_settings()

# ── Prometheus Metrics ──
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

# ── Startup time tracking ──
_start_time: float = 0.0


# ── Lifespan ──
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    global _start_time

    # Configure logging
    configure_logging(
        service_name=settings.service_name,
        log_level=settings.log_level,
        json_format=settings.json_logs,
    )
    logger = get_logger(__name__)

    # Startup
    logger.info("Starting API Service", version=settings.version, env=settings.environment)
    _start_time = time.time()

    if not ("pytest" in sys.modules or settings.environment == "testing"):
        try:
            await init_db()
            logger.info("PostgreSQL connected")
        except Exception as e:
            logger.error("PostgreSQL connection failed", error=str(e))
            raise

        try:
            await init_mongo()
            logger.info("MongoDB connected")
        except Exception as e:
            logger.error("MongoDB connection failed", error=str(e))
            raise

        try:
            await init_redis()
            logger.info("Redis connected")
        except Exception as e:
            logger.error("Redis connection failed", error=str(e))
            raise

    logger.info(
        "API Service started successfully",
        startup_time_ms=round((time.time() - _start_time) * 1000),
    )

    yield

    # Shutdown
    logger.info("Shutting down API Service")
    if not ("pytest" in sys.modules or settings.environment == "testing"):
        await close_db()
        await close_mongo()
        await close_redis()
    logger.info("API Service stopped")


# ── App ──
app = FastAPI(
    title="Scalable AI Production Infrastructure — API",
    description="Production-grade microservices platform for AI inference workloads",
    version=settings.version,
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
    lifespan=lifespan,
)

# ── CORS Middleware ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request Middleware ──
@app.middleware("http")
async def request_middleware(request: Request, call_next):
    """Add correlation ID, timing, and metrics to every request."""
    # Correlation ID
    correlation_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    set_correlation_id(correlation_id)

    # Timing
    start_time = time.time()

    # Process request
    response = await call_next(request)

    # Metrics
    duration = time.time() - start_time
    endpoint = request.url.path
    method = request.method

    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status_code=response.status_code,
    ).inc()
    REQUEST_LATENCY.labels(
        method=method,
        endpoint=endpoint,
    ).observe(duration)

    # Response headers
    response.headers["X-Request-ID"] = correlation_id
    response.headers["X-Response-Time"] = f"{duration:.4f}"

    return response


# ── Exception Handlers ──
@app.exception_handler(BaseServiceError)
async def service_error_handler(request: Request, exc: BaseServiceError) -> JSONResponse:
    """Handle custom service exceptions."""
    logger = get_logger(__name__)
    logger.warning(
        "Service error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        message=exc.message,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.error_code,
            detail=exc.message,
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unhandled exceptions."""
    logger = get_logger(__name__)
    logger.error("Unhandled exception", error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error="INTERNAL_ERROR",
            detail="An unexpected error occurred",
        ).model_dump(mode="json"),
    )


STATIC_DIR = Path(__file__).resolve().parent / "static"


# ── Operations Dashboard ──
@app.get("/", response_class=HTMLResponse, tags=["Dashboard"], include_in_schema=False)
async def root_dashboard():
    """Operations Control Center Dashboard."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse("<h1>Scalable AI Production Infrastructure</h1>")


# ── Health Endpoints ──


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check() -> HealthResponse:
    """Liveness probe — service is running."""
    return HealthResponse(
        service=ServiceName.API,
        version=settings.version,
        uptime_seconds=round(time.time() - _start_time, 2),
    )


@app.get("/ready", response_model=HealthResponse, tags=["Health"])
async def readiness_check() -> HealthResponse:
    """Readiness probe — service and dependencies are healthy."""
    checks = {
        "postgres": "healthy" if await check_db_health() else "unhealthy",
        "mongodb": "healthy" if await check_mongo_health() else "unhealthy",
        "redis": "healthy" if await check_redis_health() else "unhealthy",
    }
    all_healthy = all(v == "healthy" for v in checks.values())

    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        service=ServiceName.API,
        version=settings.version,
        uptime_seconds=round(time.time() - _start_time, 2),
        checks=checks,
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics() -> Response:
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


# ── API Routes ──
app.include_router(v1_router, prefix="/api/v1")
