# Deployment Guide — Scalable AI Production Infrastructure

## Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | v2.20+ | Local orchestration |
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.14+ | Kubernetes package manager |
| ArgoCD CLI | 2.10+ | GitOps deployment |
| uv | 0.4+ | Python package manager (optional) |

---

## Local Development

### Quick Start
```bash
git clone <repo-url>
cd scalable-ai-production-infrastructure

# One-command setup
bash scripts/setup.sh

# Or manual:
cp docker/.env.example .env    # Edit with real passwords
make dev                       # Start all services
make health                    # Verify everything is running
```

### Environment Configuration
```bash
# Required changes in .env:
POSTGRES_PASSWORD=<strong-password>
MONGO_INITDB_ROOT_PASSWORD=<strong-password>
REDIS_PASSWORD=<strong-password>
JWT_SECRET_KEY=<minimum-32-char-secret>
GRAFANA_ADMIN_PASSWORD=<strong-password>
```

### Common Development Commands
```bash
make dev            # Start with hot-reload
make test           # Run all tests
make test-api       # Run API tests only
make lint           # Check code quality
make lint-fix       # Auto-fix linting issues
make migrate        # Apply database migrations
make migrate-create MSG="add_new_table"
make logs           # Tail all logs
make logs-api       # Tail API logs only
make down           # Stop everything
make clean          # Remove containers and volumes
```

---

## Staging Deployment

### 1. Build and Push Images
```bash
# Build with commit SHA tag
./ci/scripts/build-images.sh all $(git rev-parse --short HEAD)

# Push to registry
docker push ghcr.io/your-org/api-service:$(git rev-parse --short HEAD)
docker push ghcr.io/your-org/auth-service:$(git rev-parse --short HEAD)
docker push ghcr.io/your-org/worker-service:$(git rev-parse --short HEAD)
docker push ghcr.io/your-org/inference-service:$(git rev-parse --short HEAD)
```

### 2. Create Kubernetes Secrets
```bash
kubectl create namespace scalable-ai-staging

kubectl create secret generic database-credentials \
  --namespace scalable-ai-staging \
  --from-literal=postgres-url="postgresql+asyncpg://user:pass@pg-host:5432/db" \
  --from-literal=mongo-url="mongodb://user:pass@mongo-host:27017/db" \
  --from-literal=redis-url="redis://:pass@redis-host:6379/0" \
  --from-literal=redis-broker-url="redis://:pass@redis-host:6379/1" \
  --from-literal=redis-result-url="redis://:pass@redis-host:6379/2"

kubectl create secret generic auth-secrets \
  --namespace scalable-ai-staging \
  --from-literal=jwt-secret="your-jwt-secret-minimum-32-chars"
```

### 3. Deploy with Kustomize
```bash
kubectl apply -k k8s/overlays/staging/
```

### 4. Or Deploy with Helm
```bash
helm install scalable-ai k8s/helm/scalable-ai-infra/ \
  --namespace scalable-ai-staging \
  --values k8s/helm/scalable-ai-infra/values.yaml \
  --set global.environment=staging
```

---

## Production Deployment (ArgoCD)

### 1. Install ArgoCD
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

### 2. Create ArgoCD Project
```bash
kubectl apply -f argocd/projects/scalable-ai.yaml
```

### 3. Deploy App-of-Apps
```bash
kubectl apply -f argocd/applications/app-of-apps.yaml
```

### 4. Or Use ApplicationSets for Multi-Env
```bash
kubectl apply -f argocd/applicationsets/multi-env.yaml
```

### 5. Verify Deployment
```bash
argocd app list
argocd app get scalable-ai-infra
argocd app sync scalable-ai-infra
```

---

## Rollback Procedures

### ArgoCD Rollback
```bash
# List history
argocd app history api-service-production

# Rollback to previous version
argocd app rollback api-service-production <revision>

# Or revert the Git commit
git revert <commit-sha>
git push  # ArgoCD auto-syncs
```

### Docker Compose Rollback
```bash
# Stop current
make down

# Deploy previous image
API_IMAGE_TAG=<previous-tag> make up
```

---

## Monitoring URLs

| Service | URL | Credentials |
|:--------|:----|:------------|
| Grafana | http://localhost:3000 | admin / (from .env) |
| Prometheus | http://localhost:9090 | — |
| Flower | http://localhost:5555 | — |
| API Docs | http://localhost/docs | — |
