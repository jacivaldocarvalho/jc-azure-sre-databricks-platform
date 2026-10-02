#!/usr/bin/env bash
#
# Deletes the Kind cluster.
#
set -euo pipefail

CLUSTER_NAME="jc-sre-local"

GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }

main() {
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        log_info "Deleting cluster '${CLUSTER_NAME}'..."
        kind delete cluster --name "${CLUSTER_NAME}"
        log_info "Cluster deleted."
    else
        log_info "Cluster '${CLUSTER_NAME}' does not exist."
    fi
}

main "$@"
