.PHONY: help init validate format clean terraform-init terraform-plan terraform-apply

# Default target
help:
	@echo "Available commands:"
	@echo "  make init                - Initialize project (git, env files)"
	@echo "  make validate            - Validate Terraform configurations"
	@echo "  make format              - Format Terraform and Python files"
	@echo "  make clean               - Clean temporary files"
	@echo "  make terraform-init      - Initialize Terraform (dev environment)"
	@echo "  make terraform-plan      - Plan Terraform changes (dev environment)"
	@echo "  make terraform-apply     - Apply Terraform changes (dev environment)"
	@echo "  make terraform-destroy   - Destroy Terraform resources (dev environment)"

init:
	@echo "Initializing project..."
	@test -f .env || cp .env.example .env
	@echo "Created .env file from .env.example"
	@echo "Please configure .env with your credentials"
	@mkdir -p terraform/environments/dev/.terraform
	@mkdir -p terraform/environments/staging/.terraform
	@mkdir -p terraform/environments/prod/.terraform
	@echo "Project initialized successfully"

validate:
	@echo "Validating Terraform configurations..."
	@cd terraform/environments/dev && terraform init -backend=false
	@cd terraform/environments/dev && terraform validate

format:
	@echo "Formatting Terraform files..."
	@find terraform -name "*.tf" -exec terraform fmt -write=true {} \;
	@echo "Formatting Python files..."
	@find databricks -name "*.py" -exec autopep8 --in-place {} \; 2>/dev/null || echo "autopep8 not installed, skipping Python formatting"

clean:
	@echo "Cleaning temporary files..."
	@find . -name "*.tfstate" -delete 2>/dev/null || true
	@find . -name "*.tfstate.*" -delete 2>/dev/null || true
	@find . -name "__pycache__" -type d -exec rm -rf {} \; 2>/dev/null || true
	@find . -name ".pytest_cache" -type d -exec rm -rf {} \; 2>/dev/null || true
	@rm -rf .terraform 2>/dev/null || true
	@rm -rf terraform/environments/*/.terraform 2>/dev/null || true
	@echo "Cleaning completed"

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