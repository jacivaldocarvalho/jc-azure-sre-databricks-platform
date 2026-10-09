.PHONY: help init validate format clean \
        terraform-init terraform-plan terraform-apply terraform-destroy \
        pipeline-setup pipeline-test pipeline-run pipeline-clean \
        pipeline-query lint

# Default target
help:
	@echo "JC-Azure SRE Databricks Platform - Available Commands"
	@echo ""
	@echo "Project:"
	@echo "  make init                - Initialize project (creates .env from example)"
	@echo "  make validate            - Validate Terraform configuration"
	@echo "  make format              - Format Terraform and Python files"
	@echo "  make lint                - Run Ruff linter on Python code"
	@echo "  make clean               - Clean temporary files and caches"
	@echo ""
	@echo "Terraform (dev environment):"
	@echo "  make terraform-init      - Initialize Terraform"
	@echo "  make terraform-plan      - Plan infrastructure changes"
	@echo "  make terraform-apply     - Apply infrastructure changes"
	@echo "  make terraform-destroy   - Destroy all managed resources"
	@echo ""
	@echo "Data Pipeline:"
	@echo "  make pipeline-setup      - Create Python virtualenv and install dependencies"
	@echo "  make pipeline-test       - Run pipeline unit tests"
	@echo "  make pipeline-run        - Execute the pipeline with default date range"
	@echo "  make pipeline-query      - Query the monthly aggregates Delta table"
	@echo "  make pipeline-clean      - Remove local Delta tables and caches"
	@echo ""
	@echo ""
	@echo "Kind (local Kubernetes):"
	@echo "  make kind-up            - Create Kind cluster with NGINX Ingress"
	@echo "  make kind-down          - Delete Kind cluster"
	@echo "  make kind-build         - Build and load the API image"
	@echo "  make kind-deploy        - Deploy the API via Helm"
	@echo "  make kind-status        - Show cluster, pods, and ingress status"
	@echo "  make kind-logs          - Tail API logs"
	@echo "  make kind-all           - Full setup: cluster + build + deploy"
	@echo "  make kind-monitoring        - Install Prometheus + Grafana"
	@echo "  make kind-monitoring-port-forward - Forward Grafana and Prometheus ports"
	@echo "Disaster Recovery:"
	@echo "  make protect-tfstate    - Enable versioning and soft delete on the state backend"
	@echo "  make tfstate-versions   - List available versions of the state file"

# =============================================================================
# Project targets
# =============================================================================

init:
	@echo "Initializing project..."
	@test -f .env || cp .env.example .env
	@echo "Created .env file from .env.example (if it did not exist)."
	@echo "Please configure .env with your credentials."
	@mkdir -p terraform/environments/dev/.terraform
	@mkdir -p terraform/environments/staging/.terraform
	@mkdir -p terraform/environments/prod/.terraform
	@echo "Project initialized successfully."

validate:
	@echo "Validating Terraform configurations..."
	@cd terraform/environments/dev && terraform init -backend=false
	@cd terraform/environments/dev && terraform validate

format:
	@echo "Formatting Terraform files..."
	@find terraform -name "*.tf" -exec terraform fmt -write=true {} \;
	@echo "Formatting Python files with Ruff..."
	@cd python && ruff format src/ tests/
	@echo "Applying automatic fixes..."
	@cd python && ruff check src/ tests/ --fix

lint:
	@echo "Running Ruff linter..."
	@cd python && ruff check src/ tests/

clean:
	@echo "Cleaning temporary files..."
	@find . -name "*.tfstate" -delete 2>/dev/null || true
	@find . -name "*.tfstate.*" -delete 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf terraform/environments/*/.terraform 2>/dev/null || true
	@echo "Cleanup complete."

# =============================================================================
# Terraform targets
# =============================================================================

terraform-init:
	@echo "Initializing Terraform (dev)..."
	@cd terraform/environments/dev && terraform init

terraform-plan:
	@echo "Planning Terraform changes (dev)..."
	@cd terraform/environments/dev && terraform plan

terraform-apply:
	@echo "Applying Terraform changes (dev)..."
	@cd terraform/environments/dev && terraform apply

terraform-destroy:
	@echo "Destroying Terraform resources (dev)..."
	@cd terraform/environments/dev && terraform destroy

# =============================================================================
# Data Pipeline targets
# =============================================================================

pipeline-setup:
	@echo "Setting up local Python environment..."
	@./scripts/setup-local.sh

pipeline-test:
	@echo "Running pipeline tests..."
	@cd python && . .venv/bin/activate && pytest tests/ -v

pipeline-run:
	@echo "Running the data pipeline..."
	@cd python && . .venv/bin/activate && python -m src.run_pipeline

pipeline-query:
	@echo "Querying monthly aggregates table..."
	@cd python && . .venv/bin/activate && python -c " \
from src.utils.spark import get_spark_session; \
spark = get_spark_session(); \
df = spark.read.format('delta').load('./spark-warehouse/processed/monthly_aggregates'); \
df.orderBy('series', 'year_month').show(20, truncate=False); \
spark.stop()"

pipeline-clean:
	@echo "Cleaning local pipeline artifacts..."
	@rm -rf python/spark-warehouse 2>/dev/null || true
	@rm -rf python/.pytest_cache 2>/dev/null || true
	@find python -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "Pipeline artifacts cleaned."

# =============================================================================
# Kind targets
# =============================================================================

kind-up:
	@echo "Setting up Kind cluster..."
	@./scripts/kind-setup.sh

kind-down:
	@echo "Tearing down Kind cluster..."
	@./scripts/kind-teardown.sh

kind-build:
	@echo "Building and loading the API image..."
	@./scripts/kind-build-and-load.sh

kind-deploy:
	@echo "Deploying the API to Kind..."
	@./scripts/kind-deploy.sh

kind-status:
	@echo "Cluster status:"
	@kubectl get nodes
	@echo ""
	@echo "Pods:"
	@kubectl get pods -n jc-sre
	@echo ""
	@echo "Ingress:"
	@kubectl get ingress -n jc-sre

kind-logs:
	@kubectl logs -n jc-sre -l app.kubernetes.io/name=jc-sre-api --tail=100 -f

kind-all: kind-up kind-build kind-deploy
	@echo ""
	@echo "Full deployment complete."
	@echo "Test with: curl http://jc-sre.local/health"

kind-monitoring:
	@echo "Installing monitoring stack..."
	@./scripts/kind-monitoring-up.sh

kind-monitoring-port-forward:
	@echo "Starting port-forwards..."
	@echo "Grafana will be available at http://localhost:3000 (admin/prom-operator)"
	@echo "Prometheus will be available at http://localhost:9090"
	@echo "Press Ctrl+C to stop."
	@kubectl port-forward -n jc-sre svc/jc-sre-monitoring-grafana 3000:80 & \
	 kubectl port-forward -n jc-sre svc/jc-sre-monitoring-kube-prometheus-prometheus 9090:9090

# =============================================================================
# Disaster Recovery targets
# =============================================================================

protect-tfstate:
	@echo "Protecting the Terraform state backend..."
	@./scripts/protect-tfstate-backend.sh

tfstate-versions:
	@echo "Listing state file versions..."
	@az storage blob list \
	  --container-name tfstate \
	  --account-name tfstatejcsredatabricks \
	  --auth-mode login \
	  --include v \
	  --query "[?name=='dev.terraform.tfstate'].{Version:versionId, Modified:properties.lastModified, Size:properties.contentLength}" \
	  -o table