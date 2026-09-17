# ADLS Gen2 Storage Account
resource "azurerm_storage_account" "main" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  min_tls_version                 = "TLS1_2"
  allow_nested_items_to_be_public = false

  tags = var.tags
}

# Container para dados brutos
resource "azurerm_storage_container" "raw" {
  name                  = "raw"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container para dados processados
resource "azurerm_storage_container" "processed" {
  name                  = "processed"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container para notebooks
resource "azurerm_storage_container" "notebooks" {
  name                  = "notebooks"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}

# Container para checkpoints do Databricks
resource "azurerm_storage_container" "checkpoints" {
  name                  = "checkpoints"
  storage_account_name  = azurerm_storage_account.main.name
  container_access_type = "private"
}