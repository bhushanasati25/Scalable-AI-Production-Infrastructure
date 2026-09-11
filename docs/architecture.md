# Architecture — Scalable AI Production Infrastructure

## System Overview

The platform is a **microservices architecture** designed for production AI inference workloads with 99.9% uptime targets.

## Design Principles

1. **Database-per-Service**: Each service owns its data store. PostgreSQL for structured/transactional data, MongoDB for documents/logs.
2. **Async-First**: All I/O operations use async/await (asyncpg, Motor, httpx) to maximize throughput.
3. **Repository Pattern**: Business logic is decoupled from data access, enabling testability and database swaps.
4. **Twelve-Factor App**: Config via env vars, stateless processes, disposable containers, dev/prod parity.
5. **GitOps**: Git is the single source of truth. No manual `kubectl apply`.

## Service Architecture

### API Service (Port 8000)
- **Role**: Primary REST API for clients
- **Stack**: FastAPI + SQLAlchemy 2.0 async + Motor
- **Databases**: PostgreSQL (users, tasks, jobs), MongoDB (inference logs), Redis (cache)
- **Key endpoints**: `/api/v1/tasks/`, `/api/v1/inference/`, `/api/v1/users/`

### Auth Service (Port 8001)
- **Role**: Authentication & authorization
- **Stack**: FastAPI + PyJWT + argon2
- **Database**: PostgreSQL (users table)
- **Key endpoints**: `/auth/register`, `/auth/login`, `/auth/refresh`, `/auth/me`

### Worker Service
- **Role**: Background task processing
- **Stack**: Celery + Redis (broker)
- **Queues**: `default`, `inference`, `data-pipeline`
- **Features**: Retry with exponential backoff, dead letter handling, Flower monitoring

### Inference Service (Port 8002)
- **Role**: Model serving (GPU/CPU)
- **Stack**: FastAPI + Model Registry
- **Key endpoints**: `/inference/predict`, `/inference/batch`, `/inference/models`
- **Features**: Lazy model loading, batch inference, model versioning

## Data Flow

```
Client → Nginx Gateway → API Service → PostgreSQL (write)
                                      → MongoDB (log)
                                      → Redis (cache)
                                      → Worker (via Celery) → Inference Service
```

## Network Architecture

```
[frontend] Gateway ↔ API, Auth
[backend]  API ↔ Worker ↔ Inference
[data]     Services ↔ PostgreSQL, MongoDB, Redis (internal only)
```

## Deployment Pipeline

```
Developer → Push → GitHub Actions CI → Build Images → Push to Registry
                                                     → Update Config Repo
Config Repo Update → ArgoCD Detects → Sync to Kubernetes → Rolling Update
```

## Decision Log

| Date | Decision | Rationale |
|:-----|:---------|:----------|
| Day 1 | FastAPI over Flask | Native async, auto OpenAPI, type safety |
| Day 1 | SQLAlchemy 2.0 async | Mature ORM with async support, Alembic migrations |
| Day 1 | Motor over PyMongo | Async MongoDB driver, no event loop blocking |
| Day 1 | Celery over Dramatiq | Larger ecosystem, Flower monitoring, battle-tested |
| Day 1 | Kustomize + Helm | Kustomize for overlays, Helm for distribution |
| Day 1 | ArgoCD over Flux | Richer UI, better RBAC, ApplicationSets |
| Day 1 | Prometheus over Datadog | CNCF standard, no vendor lock-in, free |
