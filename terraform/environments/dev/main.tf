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