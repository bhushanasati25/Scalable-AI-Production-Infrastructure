# Worker Service — Multi-Stage Dockerfile
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
WORKDIR /app
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser
RUN apt-get update && apt-get install -y --no-install-recommends curl libpq-dev && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
COPY pyproject.toml ./
RUN uv pip install --system --no-cache -r pyproject.toml
COPY --from=shared . /app/shared
COPY app/ ./app/


FROM base AS development
RUN uv pip install --system --no-cache ".[dev]"
ENV ENVIRONMENT=development
CMD ["celery", "-A", "app.worker", "worker", "--loglevel=info", "--concurrency=2", "-Q", "default,inference,data-pipeline"]

FROM base AS testing
RUN uv pip install --system --no-cache ".[dev]"
COPY tests/ ./tests/
RUN mkdir -p /app/reports
ENV ENVIRONMENT=testing
CMD ["pytest", "-v", "--tb=short"]

FROM base AS production
USER appuser
ENV ENVIRONMENT=production
HEALTHCHECK --interval=60s --timeout=15s --retries=3 --start-period=30s \
    CMD celery -A app.worker inspect ping --timeout 10 || exit 1
CMD ["celery", "-A", "app.worker", "worker", "--loglevel=info", "--concurrency=4", "-Q", "default,inference,data-pipeline", "--without-heartbeat", "--without-gossip", "--without-mingle"]
