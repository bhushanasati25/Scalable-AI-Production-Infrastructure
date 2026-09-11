#!/bin/bash
# ============================================================
# Build Docker Images — Multi-arch builds with caching
# Usage: ./ci/scripts/build-images.sh [service_name] [tag]
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

SERVICE="${1:-all}"
TAG="${2:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/your-org}"

build_service() {
    local svc="$1"
    local full_tag="${REGISTRY}/${svc}:${TAG}"
    local latest_tag="${REGISTRY}/${svc}:latest"

    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Building: $svc → $full_tag"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [ "$svc" = "gateway" ]; then
        docker build \
            --tag "$full_tag" \
            --tag "$latest_tag" \
            --label "org.opencontainers.image.revision=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
            --label "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --label "org.opencontainers.image.source=${CI_REPOSITORY_URL:-local}" \
            gateway/
    else
        docker build \
            --target production \
            --tag "$full_tag" \
            --tag "$latest_tag" \
            --build-context shared=shared \
            --label "org.opencontainers.image.revision=$(git rev-parse HEAD 2>/dev/null || echo 'unknown')" \
            --label "org.opencontainers.image.created=$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
            --label "org.opencontainers.image.source=${CI_REPOSITORY_URL:-local}" \
            "services/$svc"
    fi

    echo "  ✓ Built $full_tag"
    echo ""
}


case "$SERVICE" in
    api|api-service)     build_service "api-service" ;;
    auth|auth-service)   build_service "auth-service" ;;
    worker|worker-service) build_service "worker-service" ;;
    inference|inference-service) build_service "inference-service" ;;
    gateway)             build_service "gateway" ;;
    all)
        build_service "api-service"
        build_service "auth-service"
        build_service "worker-service"
        build_service "inference-service"
        build_service "gateway"
        ;;
    *)
        echo "Unknown service: $SERVICE"
        exit 1
        ;;
esac

echo "✅ All images built with tag: $TAG"
