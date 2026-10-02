#!/usr/bin/env bash
#
# Deploys the API to the Kind cluster using Helm.
#
# Usage:
#   ./scripts/kind-deploy.sh
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
RELEASE_NAME="jc-sre-api"
NAMESPACE="jc-sre"
CHART_PATH="${PROJECT_ROOT}/kubernetes/helm/jc-sre-api"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }

main() {
    # Ensure namespace exists
    kubectl create namespace "${NAMESPACE}" --dry-run=client -o yaml | kubectl apply -f -

    log_info "Deploying Helm release '${RELEASE_NAME}' to namespace '${NAMESPACE}'..."

    helm upgrade --install "${RELEASE_NAME}" "${CHART_PATH}" \
        --namespace "${NAMESPACE}" \
        --wait \
        --timeout 5m

    log_info "Deployment complete."
    echo
    log_info "Pods:"
    kubectl get pods -n "${NAMESPACE}"
    echo
    log_info "Services:"
    kubectl get svc -n "${NAMESPACE}"
    echo
    log_info "Ingress:"
    kubectl get ingress -n "${NAMESPACE}"
    echo
    log_warn "Make sure 'jc-sre.local' resolves to 127.0.0.1 in /etc/hosts."
    log_info "Then test with:"
    log_info "  curl http://jc-sre.local/health"
}

main "$@"
