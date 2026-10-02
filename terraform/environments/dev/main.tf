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

# AKS Module
#
# NOTE: The AKS cluster is not provisioned in the current environment.
# Azure for Students subscriptions have a limited credit balance, and the
# AKS Load Balancer alone costs ~$18/month even with zero nodes.
#
# The module is preserved in the codebase and validated. To activate:
#   1. Uncomment this block
#   2. Uncomment the AKS outputs below
#   3. Run terraform apply
#
# For local Kubernetes demonstration, use the Kind-based setup documented in
# docs/phases/phase-8-aks.md.
#
# See ADR-005 for the full decision record.
#
# module "aks" {
#   source = "../../modules/aks"
#
#   resource_group_name = azurerm_resource_group.main.name
#   location            = var.location
#   environment         = var.environment
#   project_name        = var.project_name
#   subnet_id           = module.networking.subnet_ids["aks"]
#   kubernetes_version  = var.kubernetes_version
#   node_vm_size        = var.node_vm_size
#   node_min_count      = 0
#   node_max_count      = 2
#   workload_node_min_count = 0
#   workload_node_max_count = 3
#   acr_id              = module.acr.registry_id
#   key_vault_id        = module.keyvault.key_vault_id
#   tags                = var.tags
# }

module "security" {
  source = "../../modules/security"

  resource_group_id                        = azurerm_resource_group.main.id
  data_lake_storage_account_id             = module.datalake.storage_account_id
  databricks_managed_identity_principal_id = module.keyvault.databricks_managed_identity_principal_id
  
  devops_principal_id                      = var.devops_principal_id
  
  # Azure OpenAI is not provisionable on Azure for Students subscriptions.
  # Set to "" to disable the role assignment. When OpenAI becomes available,
  # change this to: module.ai.account_id
  openai_account_id = ""
}

# AI Module
#
# NOTE: Azure OpenAI cannot be provisioned on Azure for Students subscriptions
# due to quota restrictions. The module is kept in the codebase for
# future use. See docs/architecture/adr-004-ai-integration.md.
#
# module "ai" {
#   source = "../../modules/ai"
#
#   resource_group_name = azurerm_resource_group.main.name
#   environment         = var.environment
#   project_name        = var.project_name
#   openai_location     = var.openai_location
#   tags                = var.tags
# }

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

# output "openai_endpoint" {
#   value = module.ai.endpoint
# }
#
# output "openai_account_name" {
#   value = module.ai.account_name
# }
#
# output "openai_deployment_name" {
#   value = module.ai.deployment_name
# }
#
# output "openai_location" {
#   value = module.ai.location
# }
#
# output "databricks_openai_role_id" {
#   value = module.security.databricks_openai_role_id
# }

# output "aks_cluster_name" {
#   value = module.aks.cluster_name
# }
#
# output "aks_cluster_fqdn" {
#   value = module.aks.cluster_fqdn
# }