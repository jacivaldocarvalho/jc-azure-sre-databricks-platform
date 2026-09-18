terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatejcsredatabricks"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"

    use_cli          = true
    use_azuread_auth = true

  }
}
