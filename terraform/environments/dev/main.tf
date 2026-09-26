# Resource Group
resource "azurerm_resource_group" "main" {
  name     = "${var.environment}-${var.project_name}-rg"
  location = var.location
  tags     = var.tags
}

# Networking Module
module "networking" {
  source = "../../modules/networking"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  project_name        = var.project_name
  vnet_address_space  = var.vnet_address_space
  subnets             = var.subnets
  tags                = var.tags
}

# Data Lake Module
module "datalake" {
  source = "../../modules/datalake"

  resource_group_name  = azurerm_resource_group.main.name
  location             = var.location
  storage_account_name = var.storage_account_name
  tags                 = var.tags
}

# Databricks Module
module "databricks" {
  source = "../../modules/databricks"

  providers = {
    databricks.workspace = databricks.workspace
  }

  resource_group_name               = azurerm_resource_group.main.name
  location                          = var.location
  environment                       = var.environment
  project_name                      = var.project_name
  vnet_id                           = module.networking.vnet_id
  public_subnet_name                = module.networking.subnet_names["databricks"]
  private_subnet_name               = module.networking.subnet_names["databricks_private"]
  public_subnet_nsg_association_id  = module.networking.nsg_association_ids["databricks"]
  private_subnet_nsg_association_id = module.networking.nsg_association_ids["databricks_private"]
  storage_account_name              = module.datalake.storage_account_name
  tags                              = var.tags
}

# Monitoring Module
module "monitoring" {
  source = "../../modules/monitoring"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  project_name        = var.project_name
  tags                = var.tags
}

# Key Vault Module
module "keyvault" {
  source = "../../modules/keyvault"

  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  project_name        = var.project_name
  tags                = var.tags
}

# Security Module
module "security" {
  source = "../../modules/security"

  resource_group_id                       = azurerm_resource_group.main.id
  data_lake_storage_account_id            = module.datalake.storage_account_id
  databricks_managed_identity_principal_id = module.keyvault.databricks_managed_identity_principal_id
  devops_principal_id                     = var.devops_principal_id
}

# Outputs
output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "vnet_id" {
  value = module.networking.vnet_id
}

output "subnet_ids" {
  value = module.networking.subnet_ids
}

output "databricks_workspace_url" {
  value = module.databricks.workspace_url
}

output "databricks_workspace_id" {
  value = module.databricks.workspace_id
}

output "storage_account_name" {
  value = module.datalake.storage_account_name
}

output "storage_account_primary_dfs_endpoint" {
  value = module.datalake.primary_dfs_endpoint
}

output "monitor_workspace_id" {
  value = module.monitoring.workspace_id
}

output "monitor_workspace_name" {
  value = module.monitoring.workspace_name
}

output "monitor_query_endpoint" {
  value = module.monitoring.query_endpoint
}

output "application_insights_connection_string" {
  value     = module.monitoring.application_insights_connection_string
  sensitive = true
}

output "key_vault_id" {
  value = module.keyvault.key_vault_id
}

output "key_vault_name" {
  value = module.keyvault.key_vault_name
}

output "key_vault_uri" {
  value = module.keyvault.key_vault_uri
}

output "databricks_managed_identity_id" {
  value = module.keyvault.databricks_managed_identity_id
}

output "databricks_managed_identity_client_id" {
  value = module.keyvault.databricks_managed_identity_client_id
}

output "databricks_storage_role_id" {
  value = module.security.databricks_storage_role_id
}

output "devops_contributor_role_id" {
  value = module.security.devops_contributor_role_id
}