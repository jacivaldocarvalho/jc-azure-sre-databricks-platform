#!/usr/bin/env bash
#
# Builds the API Docker image and loads it into the Kind cluster.
#
# Usage:
#   ./scripts/kind-build-and-load.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CLUSTER_NAME="jc-sre-local"
IMAGE_NAME="jc-sre-databricks-api"
IMAGE_TAG="latest"

GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }

main() {
    log_info "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}..."

    # Build from the python/ directory (where the Dockerfile lives)
    docker build \
        -t "${IMAGE_NAME}:${IMAGE_TAG}" \
        -f "${PROJECT_ROOT}/python/Dockerfile" \
        "${PROJECT_ROOT}/python"

    log_info "Loading image into Kind cluster '${CLUSTER_NAME}'..."
    kind load docker-image "${IMAGE_NAME}:${IMAGE_TAG}" --name "${CLUSTER_NAME}"

    log_info "Image loaded successfully."
}

main "$@"
