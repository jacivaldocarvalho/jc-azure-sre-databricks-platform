#!/usr/bin/env bash
#
# Setup script for local Python development environment.
# Creates a virtualenv, installs dependencies, and validates the setup.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PYTHON_DIR="${PROJECT_ROOT}/python"
VENV_DIR="${PYTHON_DIR}/.venv"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# Check Python version
check_python() {
    if ! command -v python3 &> /dev/null; then
        log_error "python3 not found. Please install Python 3.11 or newer."
        exit 1
    fi

    local version
    version=$(python3 --version | awk '{print $2}')
    local major minor
    major=$(echo "${version}" | cut -d. -f1)
    minor=$(echo "${version}" | cut -d. -f2)

    if [[ "${major}" -lt 3 ]] || { [[ "${major}" -eq 3 ]] && [[ "${minor}" -lt 10 ]]; }; then
        log_error "Python 3.10+ required. Found ${version}."
        exit 1
    fi

    log_info "Python ${version} detected."
}

# Check Java (required by PySpark)
check_java() {
    if ! command -v java &> /dev/null; then
        log_error "Java not found. PySpark requires Java 11 or 17."
        log_error "Install with: sudo apt install openjdk-17-jdk"
        exit 1
    fi

    local version
    version=$(java -version 2>&1 | head -n 1 | awk -F '"' '{print $2}')
    log_info "Java ${version} detected."
}

# Create virtualenv and install dependencies
setup_venv() {
    if [[ -d "${VENV_DIR}" ]]; then
        log_warn "Virtualenv already exists at ${VENV_DIR}. Reusing."
    else
        log_info "Creating virtualenv at ${VENV_DIR}..."
        python3 -m venv "${VENV_DIR}"
    fi

    log_info "Upgrading pip..."
    "${VENV_DIR}/bin/pip" install --upgrade pip

    log_info "Installing dependencies from requirements.txt..."
    "${VENV_DIR}/bin/pip" install -r "${PYTHON_DIR}/requirements.txt"

    log_info "Dependencies installed."
}

# Run smoke tests
run_tests() {
    log_info "Running smoke tests..."
    cd "${PYTHON_DIR}"
    "${VENV_DIR}/bin/pytest" tests/test_smoke.py -v
}

main() {
    log_info "Setting up local development environment..."
    check_python
    check_java
    setup_venv
    run_tests
    log_info "Setup complete."
    log_info ""
    log_info "To activate the environment:"
    log_info "  source ${VENV_DIR}/bin/activate"
    log_info ""
    log_info "To run tests:"
    log_info "  cd ${PYTHON_DIR} && pytest"
}

main "$@"
