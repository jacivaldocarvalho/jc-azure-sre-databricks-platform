output "account_id" {
  description = "ID of the Azure OpenAI account"
  value       = azurerm_cognitive_account.openai.id
}

output "account_name" {
  description = "Name of the Azure OpenAI account"
  value       = azurerm_cognitive_account.openai.name
}

output "endpoint" {
  description = "Endpoint URL of the Azure OpenAI account"
  value       = azurerm_cognitive_account.openai.endpoint
}

output "deployment_name" {
  description = "Name of the deployed model"
  value       = azurerm_cognitive_deployment.gpt4o_mini.name
}

output "location" {
  description = "Azure region of the Azure OpenAI account"
  value       = azurerm_cognitive_account.openai.location
}
