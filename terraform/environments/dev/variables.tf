variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  type        = string
  default     = "eastus"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "sredatabricks"
}

variable "storage_account_name" {
  description = "Name of the storage account for the data lake (globally unique, 3-24 chars, lowercase alphanumeric)"
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for VNet"
  type        = list(string)
  default     = ["10.0.0.0/16"]
}

variable "subnets" {
  description = "Subnet configurations"
  type = map(object({
    address_prefixes = list(string)
    service_endpoints = optional(list(string))
    private_endpoint_network_policies = optional(string)
    delegation                        = optional(string)
  }))
  default = {
    databricks = {
      address_prefixes = ["10.0.1.0/24"]
      service_endpoints = ["Microsoft.Storage"]
      delegation       = "Microsoft.Databricks/workspaces"
    }
    databricks_private = {
      address_prefixes = ["10.0.6.0/24"]
      service_endpoints = ["Microsoft.Storage"]
      delegation       = "Microsoft.Databricks/workspaces"
    }
    aks = {
      address_prefixes = ["10.0.2.0/24"]
      service_endpoints = ["Microsoft.Storage"]
    }
    data = {
      address_prefixes = ["10.0.3.0/24"]
      service_endpoints = ["Microsoft.Storage", "Microsoft.KeyVault"]
    }
    monitoring = {
      address_prefixes = ["10.0.4.0/24"]
    }
    private_endpoints = {
      address_prefixes = ["10.0.5.0/24"]
      private_endpoint_network_policies = "Enabled"
    }
  }
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
  default = {
    Environment = "dev"
    Project     = "SRE-Databricks"
    ManagedBy   = "Terraform"
  }
}
