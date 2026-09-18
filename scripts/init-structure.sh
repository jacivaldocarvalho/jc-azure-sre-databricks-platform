#!/usr/bin/env bash

set -euo pipefail

ROOT="."

echo "Criando estrutura do projeto..."

# Diretórios
directories=(
  "terraform/modules/networking"
  "terraform/modules/databricks"
  "terraform/modules/aks"
  "terraform/modules/monitoring"
  "terraform/environments/dev"
  "terraform/environments/staging"
  "terraform/environments/prod"
  "terraform/scripts"

  "azure-devops/pipelines"
  "azure-devops/templates"

  "databricks/notebooks/ingestion"
  "databricks/notebooks/processing"
  "databricks/notebooks/ml"
  "databricks/notebooks/ai"
  "databricks/jobs"
  "databricks/libraries"

  "monitoring/grafana/dashboards"
  "monitoring/grafana/datasources"
  "monitoring/prometheus"
  "monitoring/scripts"

  "security/access-control"
  "security/scripts"

  "scripts"

  "docs/architecture"
  "docs/operations"
  "docs/troubleshooting"

  "kubernetes/manifests"
  "kubernetes/helm"

  "python/src/api"
  "python/src/utils"
  "python/src/tests"
)

for dir in "${directories[@]}"; do
  mkdir -p "$ROOT/$dir"
done

# Arquivos
files=(
  # Terraform modules
  "terraform/modules/networking/main.tf"
  "terraform/modules/networking/variables.tf"
  "terraform/modules/networking/outputs.tf"

  "terraform/modules/databricks/main.tf"
  "terraform/modules/databricks/variables.tf"
  "terraform/modules/databricks/outputs.tf"

  "terraform/modules/aks/main.tf"
  "terraform/modules/aks/variables.tf"
  "terraform/modules/aks/outputs.tf"

  "terraform/modules/monitoring/main.tf"
  "terraform/modules/monitoring/variables.tf"
  "terraform/modules/monitoring/outputs.tf"

  # Terraform environments
  "terraform/environments/dev/main.tf"
  "terraform/environments/dev/terraform.tfvars"

  "terraform/environments/staging/main.tf"
  "terraform/environments/staging/terraform.tfvars"

  "terraform/environments/prod/main.tf"
  "terraform/environments/prod/terraform.tfvars"

  # Terraform scripts
  "terraform/scripts/deploy.sh"

  # Azure DevOps
  "azure-devops/pipelines/terraform-pipeline.yml"
  "azure-devops/pipelines/databricks-pipeline.yml"
  "azure-devops/pipelines/aks-pipeline.yml"

  "azure-devops/templates/terraform-template.yml"
  "azure-devops/templates/databricks-template.yml"

  # Databricks notebooks
  "databricks/notebooks/ingestion/ingest_data.py"
  "databricks/notebooks/ingestion/validate_schema.py"

  "databricks/notebooks/processing/transform_data.py"
  "databricks/notebooks/processing/feature_engineering.py"

  "databricks/notebooks/ml/train_model.py"
  "databricks/notebooks/ml/model_evaluation.py"

  "databricks/notebooks/ai/openai_integration.py"
  "databricks/notebooks/ai/azure_foundry.py"

  # Databricks jobs/libraries
  "databricks/jobs/databricks-job-config.json"
  "databricks/libraries/requirements.txt"

  # Monitoring
  "monitoring/prometheus/alerts.yml"
  "monitoring/prometheus/rules.yml"
  "monitoring/scripts/setup-monitoring.sh"

  # Security
  "security/access-control/rbac-policies.json"
  "security/access-control/managed-identities.tf"
  "security/scripts/security-scan.sh"

  # Root scripts
  "scripts/bootstrap.sh"
  "scripts/health-check.sh"
  "scripts/rollback.sh"

  # Kubernetes
  "kubernetes/manifests/deployment.yaml"
  "kubernetes/manifests/service.yaml"
  "kubernetes/manifests/ingress.yaml"
  "kubernetes/helm/values.yaml"

  # Python
  "python/requirements.txt"

  # Root files
  ".gitignore"
  "CONTRIBUTING.md"
  "LICENSE"
  "Makefile"
)

for file in "${files[@]}"; do
  touch "$ROOT/$file"
done

# Scripts executáveis
executable_files=(
  "terraform/scripts/deploy.sh"
  "monitoring/scripts/setup-monitoring.sh"
  "security/scripts/security-scan.sh"
  "scripts/bootstrap.sh"
  "scripts/health-check.sh"
  "scripts/rollback.sh"
)

for file in "${executable_files[@]}"; do
  chmod +x "$ROOT/$file"
done

echo "Estrutura criada com sucesso!"

# Exibe a estrutura, se tree estiver instalado
if command -v tree >/dev/null 2>&1; then
  tree "$ROOT"
else
  echo
  echo "Dica: instale 'tree' para visualizar a estrutura:"
  echo "  sudo apt install tree"
  echo "  tree $ROOT"
fi