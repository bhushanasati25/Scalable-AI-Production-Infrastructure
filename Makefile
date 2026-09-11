# ============================================================
# Makefile — Scalable AI Production Infrastructure
# Developer experience commands
# ============================================================

.PHONY: help up down dev test lint migrate seed logs build health clean

# Default target
help: ## Show this help message
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "  Scalable AI Production Infrastructure"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'
	@echo ""

# ── Configuration ──
COMPOSE_FILE := docker/compose.yaml
COMPOSE_DEV  := docker/compose.dev.yaml
COMPOSE_TEST := docker/compose.test.yaml
DC           := docker compose -f $(COMPOSE_FILE)
DC_DEV       := docker compose -f $(COMPOSE_FILE) -f $(COMPOSE_DEV)
DC_TEST      := docker compose -f $(COMPOSE_TEST)

# ── Environment ──
setup: ## One-command dev environment setup
	@bash scripts/setup.sh

env: ## Copy .env.example to .env (if not exists)
	@test -f .env || (cp docker/.env.example .env && echo "✓ Created .env from template")

# ── Docker Compose ──
up: env ## Start all services (production mode)
	$(DC) up -d
	@echo ""
	@echo "✓ All services started. Run 'make health' to check status."

dev: env ## Start all services (development mode with hot-reload)
	$(DC_DEV) up -d
	@echo ""
	@echo "✓ Dev environment started."
	@echo "  API:       http://localhost:8000"
	@echo "  Auth:      http://localhost:8001"
	@echo "  Inference:  http://localhost:8002"
	@echo "  Flower:    http://localhost:5555"
	@echo "  Docs:      http://localhost:80/docs"

down: ## Stop all services
	$(DC_DEV) down 2>/dev/null || true
	$(DC) down 2>/dev/null || true
	@echo "✓ All services stopped."

restart: ## Restart all services
	$(DC) restart
	@echo "✓ All services restarted."

# ── Build ──
build: ## Build all Docker images
	$(DC) build --parallel
	@echo "✓ All images built."

build-no-cache: ## Build all Docker images (no cache)
	$(DC) build --no-cache --parallel
	@echo "✓ All images rebuilt from scratch."

# ── Testing ──
test: ## Run all tests in isolated containers
	$(DC_TEST) up --build --abort-on-container-exit --exit-code-from api-service-test
	$(DC_TEST) down -v
	@echo "✓ All tests complete."

test-api: ## Run API service tests only
	$(DC_TEST) up --build --abort-on-container-exit --exit-code-from api-service-test api-service-test postgres-test mongo-test redis-test
	$(DC_TEST) down -v

test-auth: ## Run Auth service tests only
	$(DC_TEST) up --build --abort-on-container-exit --exit-code-from auth-service-test auth-service-test postgres-test redis-test
	$(DC_TEST) down -v

test-worker: ## Run Worker service tests only
	$(DC_TEST) up --build --abort-on-container-exit --exit-code-from worker-service-test worker-service-test postgres-test mongo-test redis-test
	$(DC_TEST) down -v

test-inference: ## Run Inference service tests only
	$(DC_TEST) up --build --abort-on-container-exit --exit-code-from inference-service-test inference-service-test redis-test
	$(DC_TEST) down -v

# ── Code Quality ──
lint: ## Run linting on all services
	@echo "Running ruff..."
	@for svc in api-service auth-service worker-service inference-service; do \
		echo "  → services/$$svc"; \
		cd services/$$svc && uv run ruff check . && uv run ruff format --check . && cd ../..; \
	done
	@echo "✓ All linting passed."

lint-fix: ## Fix linting issues automatically
	@for svc in api-service auth-service worker-service inference-service; do \
		echo "  → Fixing services/$$svc"; \
		cd services/$$svc && uv run ruff check --fix . && uv run ruff format . && cd ../..; \
	done
	@echo "✓ All linting issues fixed."

typecheck: ## Run type checking on all services
	@for svc in api-service auth-service worker-service inference-service; do \
		echo "  → Type checking services/$$svc"; \
		cd services/$$svc && uv run mypy app && cd ../..; \
	done
	@echo "✓ Type checking passed."

# ── Database ──
migrate: ## Run database migrations
	$(DC) exec api-service alembic upgrade head
	@echo "✓ Migrations applied."

migrate-create: ## Create new migration (usage: make migrate-create MSG="add users table")
	$(DC) exec api-service alembic revision --autogenerate -m "$(MSG)"
	@echo "✓ Migration created."

migrate-rollback: ## Rollback last migration
	$(DC) exec api-service alembic downgrade -1
	@echo "✓ Last migration rolled back."

seed: ## Seed development data
	@bash scripts/seed-db.sh
	@echo "✓ Database seeded."

# ── Monitoring ──
health: ## Check health of all services
	@bash docker/scripts/healthcheck.sh all

logs: ## Tail logs from all services
	$(DC) logs -f --tail=100

logs-api: ## Tail API service logs
	$(DC) logs -f --tail=100 api-service

logs-worker: ## Tail Worker service logs
	$(DC) logs -f --tail=100 worker-service

logs-inference: ## Tail Inference service logs
	$(DC) logs -f --tail=100 inference-service

ps: ## Show running containers
	$(DC) ps

# ── Benchmarks & Resilience ──
benchmark: ## Run DBaaS 35% latency acceleration benchmark
	@python3 benchmarks/latency_benchmark.py

load-test: ## Run high-concurrency Kubernetes autoscaling load test
	@python3 benchmarks/load_test.py

chaos: ## Run chaos engineering & fault-tolerance drill
	@bash scripts/chaos-drill.sh


# ── Cleanup ──
clean: ## Remove containers, volumes, and images
	$(DC) down -v --rmi local --remove-orphans
	@echo "✓ Cleaned up containers, volumes, and local images."

clean-all: ## Remove everything including named volumes (⚠️  DESTROYS DATA)
	$(DC) down -v --rmi all --remove-orphans
	docker volume rm -f sai-postgres-data sai-mongo-data sai-redis-data sai-model-data 2>/dev/null || true
	@echo "⚠️  All data destroyed."

prune: ## Docker system prune (dangling images, stopped containers)
	docker system prune -f
	@echo "✓ Docker system pruned."
