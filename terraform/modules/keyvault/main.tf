terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Data source for the current Azure client
data "azurerm_client_config" "current" {}

# Key Vault with RBAC authorization
resource "azurerm_key_vault" "main" {
  name                       = "${var.environment}-${var.project_name}-kv"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = data.azurerm_client_config.current.tenant_id
  sku_name                   = "standard"
  purge_protection_enabled   = false
  soft_delete_retention_days = 7
  enable_rbac_authorization  = true

  network_acls {
    default_action = "Allow"
    bypass         = "AzureServices"
  }

  tags = var.tags
}

# Grant the current user administrative access (for managing secrets)
resource "azurerm_role_assignment" "current_user_admin" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Administrator"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Managed Identity for the Databricks workspace to read secrets
resource "azurerm_user_assigned_identity" "databricks" {
  name                = "${var.environment}-${var.project_name}-dbw-mi"
  location            = var.location
  resource_group_name = var.resource_group_name
  tags                = var.tags
}

# Grant the Databricks Managed Identity read access to secrets
resource "azurerm_role_assignment" "databricks_secrets_user" {
  scope                = azurerm_key_vault.main.id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_user_assigned_identity.databricks.principal_id
}
