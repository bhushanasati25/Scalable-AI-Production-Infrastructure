#!/bin/bash
# ============================================================
# Run Tests — Parallel test execution per service
# Usage: ./ci/scripts/run-tests.sh [service_name]
# ============================================================
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$PROJECT_ROOT"

SERVICE="${1:-all}"
COVERAGE_THRESHOLD=80
EXIT_CODE=0

run_service_tests() {
    local svc="$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  Testing: $svc"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    cd "$PROJECT_ROOT/services/$svc"

    # Install dependencies if running locally
    if command -v uv &> /dev/null; then
        uv pip install --system ".[dev]" 2>/dev/null || true
    fi

    # Run tests
    mkdir -p reports "$PROJECT_ROOT/reports"
    python -m pytest \
        -v \
        --tb=short \
        --junitxml="$PROJECT_ROOT/reports/junit-${svc}.xml" \
        --cov=app \
        --cov-report=xml:"$PROJECT_ROOT/reports/coverage-${svc}.xml" \
        --cov-report=term-missing \
        tests/ || EXIT_CODE=1


    cd "$PROJECT_ROOT"
    echo ""
}

# Create reports directory
mkdir -p "$PROJECT_ROOT/reports"

case "$SERVICE" in
    api|api-service)
        run_service_tests "api-service"
        ;;
    auth|auth-service)
        run_service_tests "auth-service"
        ;;
    worker|worker-service)
        run_service_tests "worker-service"
        ;;
    inference|inference-service)
        run_service_tests "inference-service"
        ;;
    all)
        for svc in api-service auth-service worker-service inference-service; do
            run_service_tests "$svc"
        done
        ;;
    *)
        echo "Unknown service: $SERVICE"
        echo "Usage: $0 [api|auth|worker|inference|all]"
        exit 1
        ;;
esac

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "  ✅ All tests passed!"
else
    echo "  ❌ Some tests failed!"
fi
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

exit $EXIT_CODE
