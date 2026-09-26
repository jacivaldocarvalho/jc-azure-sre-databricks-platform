output "databricks_storage_role_id" {
  description = "ID of the Storage Blob Data Contributor assignment for Databricks"
  value       = azurerm_role_assignment.databricks_storage.id
}

output "devops_contributor_role_id" {
  description = "ID of the Contributor assignment for Azure DevOps at the Resource Group"
  value       = length(azurerm_role_assignment.devops_contributor_rg) > 0 ? azurerm_role_assignment.devops_contributor_rg[0].id : null
}
