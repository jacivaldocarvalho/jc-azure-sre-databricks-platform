output "workspace_id" {
  description = "ID of the Azure Monitor workspace"
  value       = azurerm_monitor_workspace.main.id
}

output "workspace_name" {
  description = "Name of the Azure Monitor workspace"
  value       = azurerm_monitor_workspace.main.name
}

output "query_endpoint" {
  description = "Query endpoint of the Azure Monitor workspace"
  value       = azurerm_monitor_workspace.main.query_endpoint
}

output "application_insights_connection_string" {
  description = "Connection string for the Application Insights resource"
  value       = azurerm_application_insights.main.connection_string
  sensitive   = true
}