# Databricks Workspace com VNet Injection
resource "azurerm_databricks_workspace" "main" {
  name                        = "${var.environment}-${var.project_name}-dbw"
  resource_group_name         = var.resource_group_name
  location                    = var.location
  sku                         = "premium"
  managed_resource_group_name = "${var.environment}-${var.project_name}-dbw-managed-rg"

  custom_parameters {
    virtual_network_id                                   = var.vnet_id
    public_subnet_name                                   = var.public_subnet_name
    private_subnet_name                                  = var.private_subnet_name
    public_subnet_network_security_group_association_id  = var.public_subnet_nsg_association_id
    private_subnet_network_security_group_association_id = var.private_subnet_nsg_association_id
    no_public_ip                                         = false
    storage_account_name                                 = "${var.storage_account_name}dbw"
    storage_account_sku_name                             = "Standard_LRS"
  }

  tags = var.tags
}