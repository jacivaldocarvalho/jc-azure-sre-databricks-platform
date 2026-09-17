output "workspace_id" {
  description = "ID of the Databricks Workspace"
  value       = azurerm_databricks_workspace.main.id
}

output "workspace_url" {
  description = "URL of the Databricks Workspace"
  value       = azurerm_databricks_workspace.main.workspace_url
}

output "workspace_name" {
  description = "Name of the Databricks Workspace"
  value       = azurerm_databricks_workspace.main.name
}