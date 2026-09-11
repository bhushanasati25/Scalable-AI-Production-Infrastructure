# ============================================================
# API Service — Multi-Stage Dockerfile
# Stages: base → development → testing → production
# ============================================================

# ── Base Stage ──
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Security: create non-root user
RUN groupadd -r appuser && \
    useradd -r -g appuser -d /app -s /sbin/nologin appuser

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy dependency files
COPY pyproject.toml ./

# Install production dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy shared library
COPY --from=shared . /app/shared


# Copy application code
COPY app/ ./app/

# ── Development Stage ──
FROM base AS development

# Install dev dependencies
RUN uv pip install --system --no-cache ".[dev]"

# Dev runs with reload
ENV ENVIRONMENT=development
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# ── Testing Stage ──
FROM base AS testing

# Install dev/test dependencies
RUN uv pip install --system --no-cache ".[dev]"

# Copy test files
COPY tests/ ./tests/
COPY alembic/ ./alembic/ 
COPY alembic.ini ./

RUN mkdir -p /app/reports

ENV ENVIRONMENT=testing
CMD ["pytest", "-v", "--tb=short"]

# ── Production Stage ──
FROM base AS production

# Copy Alembic for migrations
COPY alembic/ ./alembic/
COPY alembic.ini ./

# Switch to non-root user
USER appuser

# Production runs with multiple workers
ENV ENVIRONMENT=production
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=30s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "4", \
     "--log-level", "info", \
     "--access-log", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
