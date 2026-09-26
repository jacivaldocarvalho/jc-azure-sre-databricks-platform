output "key_vault_id" {
  description = "ID of the Key Vault"
  value       = azurerm_key_vault.main.id
}

output "key_vault_name" {
  description = "Name of the Key Vault"
  value       = azurerm_key_vault.main.name
}

output "key_vault_uri" {
  description = "URI of the Key Vault"
  value       = azurerm_key_vault.main.vault_uri
}

output "databricks_managed_identity_id" {
  description = "ID of the User-Assigned Managed Identity for Databricks"
  value       = azurerm_user_assigned_identity.databricks.id
}

output "databricks_managed_identity_principal_id" {
  description = "Principal ID of the User-Assigned Managed Identity for Databricks"
  value       = azurerm_user_assigned_identity.databricks.principal_id
}

output "databricks_managed_identity_client_id" {
  description = "Client ID of the User-Assigned Managed Identity for Databricks"
  value       = azurerm_user_assigned_identity.databricks.client_id
}
