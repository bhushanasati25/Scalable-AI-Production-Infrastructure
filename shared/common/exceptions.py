"""
Custom exception hierarchy for Scalable AI Production Infrastructure.
Provides consistent error handling across all microservices.
"""

from __future__ import annotations

from typing import Any


class BaseServiceError(Exception):
    """Base exception for all service errors."""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: str = "INTERNAL_ERROR",
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


# ── Client Errors (4xx) ──

class BadRequestError(BaseServiceError):
    def __init__(self, message: str = "Bad request", details: dict[str, Any] | None = None):
        super().__init__(message, status_code=400, error_code="BAD_REQUEST", details=details)


class UnauthorizedError(BaseServiceError):
    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, status_code=401, error_code="UNAUTHORIZED")


class ForbiddenError(BaseServiceError):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message, status_code=403, error_code="FORBIDDEN")


class NotFoundError(BaseServiceError):
    def __init__(self, resource: str = "Resource", resource_id: str = ""):
        message = f"{resource} not found"
        if resource_id:
            message = f"{resource} '{resource_id}' not found"
        super().__init__(
            message,
            status_code=404,
            error_code="NOT_FOUND",
            details={"resource": resource, "resource_id": resource_id},
        )


class ConflictError(BaseServiceError):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message, status_code=409, error_code="CONFLICT")


class RateLimitError(BaseServiceError):
    def __init__(self, retry_after: int = 60):
        super().__init__(
            "Rate limit exceeded",
            status_code=429,
            error_code="RATE_LIMIT_EXCEEDED",
            details={"retry_after_seconds": retry_after},
        )


class ValidationError(BaseServiceError):
    def __init__(self, message: str = "Validation error", errors: list[dict[str, Any]] | None = None):
        super().__init__(
            message,
            status_code=422,
            error_code="VALIDATION_ERROR",
            details={"errors": errors or []},
        )


# ── Server Errors (5xx) ──

class InternalError(BaseServiceError):
    def __init__(self, message: str = "Internal server error"):
        super().__init__(message, status_code=500, error_code="INTERNAL_ERROR")


class DatabaseError(BaseServiceError):
    def __init__(self, message: str = "Database operation failed"):
        super().__init__(message, status_code=503, error_code="DATABASE_ERROR")


class ExternalServiceError(BaseServiceError):
    def __init__(self, service: str, message: str = "External service unavailable"):
        super().__init__(
            f"{service}: {message}",
            status_code=502,
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class InferenceError(BaseServiceError):
    def __init__(self, message: str = "Inference failed", model: str = ""):
        super().__init__(
            message,
            status_code=500,
            error_code="INFERENCE_ERROR",
            details={"model": model},
        )


class InferenceTimeoutError(BaseServiceError):
    def __init__(self, timeout: int = 60, model: str = ""):
        super().__init__(
            f"Inference timed out after {timeout}s",
            status_code=504,
            error_code="INFERENCE_TIMEOUT",
            details={"timeout_seconds": timeout, "model": model},
        )
