#!/bin/bash
# ============================================================
# Unified Health Check Script
# Usage: ./healthcheck.sh <service_name>
# ============================================================
set -euo pipefail

SERVICE="${1:-all}"
HEALTHY=0
UNHEALTHY=0

check_http() {
    local name="$1"
    local url="$2"
    if curl -sf --max-time 5 "$url" > /dev/null 2>&1; then
        echo "  ✓ $name is healthy"
        ((HEALTHY++))
    else
        echo "  ✗ $name is unhealthy"
        ((UNHEALTHY++))
    fi
}

check_postgres() {
    if pg_isready -h "${POSTGRES_HOST:-postgres}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER:-app_user}" > /dev/null 2>&1; then
        echo "  ✓ PostgreSQL is healthy"
        ((HEALTHY++))
    else
        echo "  ✗ PostgreSQL is unhealthy"
        ((UNHEALTHY++))
    fi
}

check_mongo() {
    if mongosh --host "${MONGO_HOST:-mongo}" --port "${MONGO_PORT:-27017}" \
        --username "${MONGO_INITDB_ROOT_USERNAME:-admin}" \
        --password "${MONGO_INITDB_ROOT_PASSWORD}" \
        --authenticationDatabase admin \
        --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
        echo "  ✓ MongoDB is healthy"
        ((HEALTHY++))
    else
        echo "  ✗ MongoDB is unhealthy"
        ((UNHEALTHY++))
    fi
}

check_redis() {
    if redis-cli -h "${REDIS_HOST:-redis}" -p "${REDIS_PORT:-6379}" \
        -a "${REDIS_PASSWORD:-}" ping 2>/dev/null | grep -q PONG; then
        echo "  ✓ Redis is healthy"
        ((HEALTHY++))
    else
        echo "  ✗ Redis is unhealthy"
        ((UNHEALTHY++))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Health Check — Scalable AI Infrastructure"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

case "$SERVICE" in
    api)
        check_http "API Service" "http://localhost:${API_PORT:-8000}/health"
        ;;
    auth)
        check_http "Auth Service" "http://localhost:${AUTH_PORT:-8001}/health"
        ;;
    inference)
        check_http "Inference Service" "http://localhost:${INFERENCE_PORT:-8002}/health"
        ;;
    postgres)
        check_postgres
        ;;
    mongo)
        check_mongo
        ;;
    redis)
        check_redis
        ;;
    all|*)
        echo ""
        echo "  Services:"
        check_http "API Service" "http://localhost:${API_PORT:-8000}/health"
        check_http "Auth Service" "http://localhost:${AUTH_PORT:-8001}/health"
        check_http "Inference Service" "http://localhost:${INFERENCE_PORT:-8002}/health"
        echo ""
        echo "  Data Stores:"
        check_postgres
        check_mongo
        check_redis
        echo ""
        echo "  Monitoring:"
        check_http "Prometheus" "http://localhost:${PROMETHEUS_PORT:-9090}/-/healthy"
        check_http "Grafana" "http://localhost:${GRAFANA_PORT:-3000}/api/health"
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Results: $HEALTHY healthy, $UNHEALTHY unhealthy"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

[ "$UNHEALTHY" -eq 0 ] && exit 0 || exit 1
