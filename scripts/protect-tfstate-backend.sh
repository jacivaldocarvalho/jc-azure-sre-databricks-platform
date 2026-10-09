#!/usr/bin/env bash
#
# Enables protection features on the Terraform state backend.
#
# This script is idempotent: it can be run multiple times without
# changing the outcome. It enables:
#
#   - Blob versioning: retains previous versions of the state file
#   - Blob soft delete: retains deleted blobs for a grace period
#   - Container soft delete: retains deleted containers for a grace period
#
# These features protect against:
#   - Accidental corruption of the state (rollback to a previous version)
#   - Accidental deletion of the state blob (recover within the grace period)
#   - Accidental deletion of the container (recover within the grace period)
#
# Usage:
#   ./scripts/protect-tfstate-backend.sh
#
set -euo pipefail

# Configuration
RESOURCE_GROUP="tfstate-rg"
STORAGE_ACCOUNT="tfstatejcsredatabricks"
BLOB_RETENTION_DAYS=30
CONTAINER_RETENTION_DAYS=30

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check prerequisites
check_prerequisites() {
    if ! command -v az &> /dev/null; then
        log_error "Azure CLI (az) is not installed."
        exit 1
    fi

    if ! az account show &> /dev/null; then
        log_error "Not logged in to Azure. Run 'az login' first."
        exit 1
    fi

    log_info "Prerequisites OK."
}

# Verify that the backend exists
check_backend() {
    log_info "Verifying that the backend exists..."

    if ! az storage account show \
        --name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --query "id" -o tsv &> /dev/null; then
        log_error "Storage account '${STORAGE_ACCOUNT}' not found in '${RESOURCE_GROUP}'."
        exit 1
    fi

    log_info "Backend '${STORAGE_ACCOUNT}' found."
}

# Enable blob versioning and soft delete
enable_blob_protection() {
    log_info "Enabling blob versioning and soft delete..."

    az storage account blob-service-properties update \
        --account-name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --enable-versioning true \
        --enable-delete-retention true \
        --delete-retention-days "${BLOB_RETENTION_DAYS}" \
        --output none

    log_info "Blob versioning: enabled."
    log_info "Blob soft delete: enabled (${BLOB_RETENTION_DAYS} days)."
}

# Enable container soft delete
enable_container_protection() {
    log_info "Enabling container soft delete..."

    az storage account blob-service-properties update \
        --account-name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --enable-container-delete-retention true \
        --container-delete-retention-days "${CONTAINER_RETENTION_DAYS}" \
        --output none

    log_info "Container soft delete: enabled (${CONTAINER_RETENTION_DAYS} days)."
}

# Display current configuration
show_configuration() {
    echo
    log_info "======================================================"
    log_info "Current backend protection configuration"
    log_info "======================================================"
    echo

    az storage account blob-service-properties show \
        --account-name "${STORAGE_ACCOUNT}" \
        --resource-group "${RESOURCE_GROUP}" \
        --query "{
            Versioning:isVersioningEnabled,
            BlobSoftDelete:deleteRetentionPolicy.enabled,
            BlobRetentionDays:deleteRetentionPolicy.days,
            ContainerSoftDelete:containerDeleteRetentionPolicy.enabled,
            ContainerRetentionDays:containerDeleteRetentionPolicy.days
        }" \
        -o table

    echo
    log_info "To verify versioning manually:"
    log_info "  az storage blob list \\"
    log_info "    --container-name tfstate \\"
    log_info "    --account-name ${STORAGE_ACCOUNT} \\"
    log_info "    --auth-mode login \\"
    log_info "    --include v"
    echo
}

# Main entry point
main() {
    check_prerequisites
    check_backend
    enable_blob_protection
    enable_container_protection
    show_configuration

    log_info "Backend protection complete."
    echo
    log_info "Related documentation:"
    log_info "  docs/operations/runbooks/recover-terraform-state.md"
    echo
}

main "$@"
