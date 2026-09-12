"""
Shared Pydantic schemas used across all microservices.
Provides consistent request/response models and validation.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# ── Enums ──


class ServiceName(StrEnum):
    API = "api-service"
    AUTH = "auth-service"
    WORKER = "worker-service"
    INFERENCE = "inference-service"


class TaskStatus(StrEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class InferenceDevice(StrEnum):
    CPU = "cpu"
    CUDA = "cuda"
    MPS = "mps"  # Apple Silicon


# ── Base Models ──


class TimestampMixin(BaseModel):
    """Mixin for created_at / updated_at timestamps."""

    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


class BaseSchema(BaseModel):
    """Base schema with strict config for all models."""

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True,
    )


# ── Health Check ──


class HealthResponse(BaseSchema):
    status: str = "healthy"
    service: ServiceName
    version: str = "0.1.0"
    uptime_seconds: float = 0.0
    checks: dict[str, str] = Field(default_factory=dict)


# ── Pagination ──

T = TypeVar("T")


class PaginatedResponse(BaseSchema, Generic[T]):
    items: list[T]
    total: int
    page: int = 1
    page_size: int = 20
    pages: int = 1


# ── API Response Wrapper ──


class APIResponse(BaseSchema, Generic[T]):
    success: bool = True
    data: T | None = None
    message: str | None = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class ErrorResponse(BaseSchema):
    success: bool = False
    error: str
    detail: str | None = None
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


# ── User Models ──


class UserBase(BaseSchema):
    email: str = Field(..., min_length=5, max_length=255)
    full_name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8, max_length=128)


class UserResponse(UserBase, TimestampMixin):
    id: uuid.UUID
    role: str = "user"


# ── Task Models ──


class TaskCreate(BaseSchema):
    name: str = Field(..., min_length=1, max_length=255)
    task_type: str = Field(..., min_length=1, max_length=100)
    payload: dict[str, Any] = Field(default_factory=dict)
    priority: int = Field(default=0, ge=0, le=10)


class TaskResponse(BaseSchema, TimestampMixin):
    id: uuid.UUID
    name: str
    task_type: str
    status: TaskStatus = TaskStatus.PENDING
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error_message: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


# ── Inference Models ──


class InferenceRequest(BaseSchema):
    model_name: str = Field(..., min_length=1, max_length=255)
    input_data: dict[str, Any]
    parameters: dict[str, Any] = Field(default_factory=dict)
    timeout: int = Field(default=60, ge=1, le=600)


class InferenceResponse(BaseSchema):
    request_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    model_name: str
    status: TaskStatus
    output: dict[str, Any] | None = None
    latency_ms: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


# ── Auth Models ──


class TokenPayload(BaseSchema):
    sub: str  # User ID
    exp: datetime
    iat: datetime
    jti: str  # JWT ID for revocation
    role: str = "user"
    scopes: list[str] = Field(default_factory=list)


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
