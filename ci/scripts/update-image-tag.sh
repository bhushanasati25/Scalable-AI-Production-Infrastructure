#!/bin/bash
# ============================================================
# Update Image Tag — Updates Kustomize image tag for GitOps
# Usage: ./ci/scripts/update-image-tag.sh <service> <new_tag>
# ============================================================
set -euo pipefail

SERVICE="${1:?Usage: $0 <service> <new_tag>}"
NEW_TAG="${2:?Usage: $0 <service> <new_tag>}"
REGISTRY="${DOCKER_REGISTRY:-ghcr.io/your-org}"

echo "Updating $SERVICE to tag $NEW_TAG"

# Update Kustomize image tags for each environment
for ENV in staging production; do
    OVERLAY_DIR="k8s/overlays/$ENV"

    if [ -d "$OVERLAY_DIR" ]; then
        cd "$OVERLAY_DIR"

        # Use kustomize to update the image tag
        if command -v kustomize &> /dev/null; then
            kustomize edit set image "${SERVICE}=${REGISTRY}/${SERVICE}:${NEW_TAG}"
            echo "  ✓ Updated $ENV overlay"
        else
            echo "  ⚠ kustomize not found, updating manually"
            # Fallback: use yq or sed
            if command -v yq &> /dev/null; then
                yq -i ".images += [{\"name\": \"${SERVICE}\", \"newName\": \"${REGISTRY}/${SERVICE}\", \"newTag\": \"${NEW_TAG}\"}]" kustomization.yaml
            fi
        fi

        cd - > /dev/null
    fi
done

echo ""
echo "✅ Image tag updated: ${SERVICE} → ${NEW_TAG}"
echo "   ArgoCD will auto-sync this change."
