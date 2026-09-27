terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# Azure OpenAI Service account
resource "azurerm_cognitive_account" "openai" {
  name                = "${var.environment}-${var.project_name}-openai"
  location            = var.openai_location
  resource_group_name = var.resource_group_name
  kind                = "OpenAI"
  sku_name            = "S0"

  custom_subdomain_name         = "${var.environment}-${var.project_name}-openai"
  public_network_access_enabled = true

  tags = var.tags
}

# Model deployment: gpt-4o-mini
resource "azurerm_cognitive_deployment" "gpt4o_mini" {
  name                 = "gpt-4o-mini"
  cognitive_account_id = azurerm_cognitive_account.openai.id

  model {
    format  = "OpenAI"
    name    = "gpt-4o-mini"
    version = "2024-07-18"
  }

  scale {
    type     = "GlobalStandard"
    capacity = 10
  }
}
