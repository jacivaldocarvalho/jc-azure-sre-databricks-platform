output "storage_account_id" {
  description = "ID of the storage account"
  value       = azurerm_storage_account.main.id
}

output "storage_account_name" {
  description = "Name of the storage account"
  value       = azurerm_storage_account.main.name
}

output "primary_dfs_endpoint" {
  description = "Primary DFS endpoint (ADLS Gen2)"
  value       = azurerm_storage_account.main.primary_dfs_endpoint
}