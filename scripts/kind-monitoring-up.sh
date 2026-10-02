#!/usr/bin/env bash
#
# Installs or upgrades the monitoring stack (Prometheus + Grafana) in the
# Kind cluster.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
CHART_PATH="${PROJECT_ROOT}/kubernetes/helm/jc-sre-monitoring"
NAMESPACE="jc-sre"
RELEASE="jc-sre-monitoring"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }

main() {
    log_info "Updating Helm dependencies..."
    helm dependency update "${CHART_PATH}"

    log_info "Installing/upgrading monitoring stack (this may take 3-5 minutes)..."
    helm upgrade --install "${RELEASE}" "${CHART_PATH}" \
        --namespace "${NAMESPACE}" \
        --create-namespace \
        --wait \
        --timeout 10m

    log_info "Monitoring stack deployed."
    echo
    log_info "Pods:"
    kubectl get pods -n "${NAMESPACE}" -l "release=${RELEASE}"
    echo
    log_warn "To access Grafana:"
    log_warn "  kubectl port-forward -n ${NAMESPACE} svc/${RELEASE}-grafana 3000:80"
    log_warn "  Open http://localhost:3000 (admin / prom-operator)"
    echo
    log_warn "To access Prometheus:"
    log_warn "  kubectl port-forward -n ${NAMESPACE} svc/${RELEASE}-kube-prometheus-prometheus 9090:9090"
    log_warn "  Open http://localhost:9090"
}

main "$@"
