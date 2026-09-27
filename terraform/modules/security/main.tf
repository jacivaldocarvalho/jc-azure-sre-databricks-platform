terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Data source to reference the current subscription
data "azurerm_subscription" "current" {}

# =============================================================================
# Role assignments for the Databricks Managed Identity on the Data Lake
# =============================================================================

# Grant the Databricks Managed Identity Storage Blob Data Contributor on the
# Data Lake Storage Account. This allows the workspace to read and write
# to the containers without using shared account keys.
resource "azurerm_role_assignment" "databricks_storage" {
  scope                = var.data_lake_storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.databricks_managed_identity_principal_id

  description = "Allow Databricks workspace to read and write to the Data Lake"
}

# =============================================================================
# Role assignments for external service principals
# =============================================================================

# The Azure DevOps Service Principal is granted Contributor at the Resource
# Group scope instead of the Subscription scope. This follows the principle
# of least privilege while allowing the CI/CD pipeline to manage all
# resources in the project's Resource Group.
resource "azurerm_role_assignment" "devops_contributor_rg" {
  count = var.devops_principal_id != "" ? 1 : 0

  scope                = var.resource_group_id
  role_definition_name = "Contributor"
  principal_id         = var.devops_principal_id

  description = "Allow Azure DevOps pipelines to manage resources in the project Resource Group"
}

# =============================================================================
# Role assignments for the Azure OpenAI resource
# =============================================================================

# Grant the Databricks Managed Identity the ability to invoke the
# deployed OpenAI model. Uses the least-privilege role for inference.
#
# The count expression makes this resource conditional: when
# openai_account_id is empty (OpenAI not provisioned), the resource
# is not created.
resource "azurerm_role_assignment" "databricks_openai_user" {
  count = var.openai_account_id != "" ? 1 : 0

  scope                = var.openai_account_id
  role_definition_name = "Cognitive Services OpenAI User"
  principal_id         = var.databricks_managed_identity_principal_id

  description = "Allow Databricks Managed Identity to invoke OpenAI models"
}