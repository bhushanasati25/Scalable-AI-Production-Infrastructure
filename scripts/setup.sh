#!/bin/bash
# ============================================================
# One-Command Development Setup
# Usage: bash scripts/setup.sh
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Scalable AI Production Infrastructure Setup"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── Check Prerequisites ──
echo "→ Checking prerequisites..."

check_command() {
    if command -v "$1" &> /dev/null; then
        echo "  ✓ $1 found: $($1 --version 2>&1 | head -n1)"
    else
        echo "  ✗ $1 not found. Please install it first."
        exit 1
    fi
}

check_command docker
check_command git

# Check Docker daemon
if ! docker info &> /dev/null; then
    echo "  ✗ Docker daemon is not running. Start Docker Desktop first."
    exit 1
fi
echo "  ✓ Docker daemon is running"

# Optional: check uv
if command -v uv &> /dev/null; then
    echo "  ✓ uv found: $(uv --version 2>&1)"
else
    echo "  ⚠ uv not found (optional — used for local development)"
fi

echo ""

# ── Environment Configuration ──
echo "→ Setting up environment..."

if [ ! -f .env ]; then
    cp docker/.env.example .env
    echo "  ✓ Created .env from template"
    echo "  ⚠ IMPORTANT: Edit .env and set real passwords before production use!"
else
    echo "  ✓ .env already exists"
fi

echo ""

# ── Make Scripts Executable ──
echo "→ Setting permissions..."
chmod +x docker/scripts/*.sh 2>/dev/null || true
chmod +x scripts/*.sh 2>/dev/null || true
chmod +x ci/scripts/*.sh 2>/dev/null || true
echo "  ✓ Scripts are executable"
echo ""

# ── Build Docker Images ──
echo "→ Building Docker images (this may take a few minutes)..."
docker compose -f docker/compose.yaml build --parallel
echo "  ✓ All images built"
echo ""

# ── Start Services ──
echo "→ Starting services..."
docker compose -f docker/compose.yaml -f docker/compose.dev.yaml up -d
echo "  ✓ All services starting"
echo ""

# ── Wait for Health ──
echo "→ Waiting for services to become healthy..."
MAX_RETRIES=30
RETRY_INTERVAL=5

for i in $(seq 1 $MAX_RETRIES); do
    HEALTHY=$(docker compose -f docker/compose.yaml ps --format json 2>/dev/null | grep -c '"healthy"' || echo "0")
    TOTAL=$(docker compose -f docker/compose.yaml ps --format json 2>/dev/null | wc -l | tr -d ' ' || echo "0")

    if [ "$HEALTHY" -ge 3 ]; then
        echo "  ✓ Core services are healthy ($HEALTHY/$TOTAL)"
        break
    fi

    if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "  ⚠ Timed out waiting for services. Run 'make health' to check."
        break
    fi

    echo "  Waiting... ($i/$MAX_RETRIES) — $HEALTHY/$TOTAL healthy"
    sleep $RETRY_INTERVAL
done

echo ""

# ── Summary ──
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Setup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  🌐 API Gateway:   http://localhost:80"
echo "  📡 API Service:   http://localhost:8000"
echo "  🔐 Auth Service:  http://localhost:8001"
echo "  🤖 Inference:     http://localhost:8002"
echo "  🌸 Flower:        http://localhost:5555"
echo "  📖 API Docs:      http://localhost:80/docs"
echo ""
echo "  Useful commands:"
echo "    make dev       — Start dev environment"
echo "    make test      — Run all tests"
echo "    make logs      — Tail service logs"
echo "    make health    — Check service health"
echo "    make help      — Show all commands"
echo ""
