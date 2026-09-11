# Auth Service — Multi-Stage Dockerfile
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
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]

FROM base AS testing
RUN uv pip install --system --no-cache ".[dev]"
COPY tests/ ./tests/
RUN mkdir -p /app/reports
ENV ENVIRONMENT=testing
CMD ["pytest", "-v", "--tb=short"]

FROM base AS production
USER appuser
ENV ENVIRONMENT=production
EXPOSE 8001
HEALTHCHECK --interval=30s --timeout=10s --retries=3 --start-period=20s \
    CMD curl -f http://localhost:8001/health || exit 1
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001", "--workers", "2", "--proxy-headers"]
