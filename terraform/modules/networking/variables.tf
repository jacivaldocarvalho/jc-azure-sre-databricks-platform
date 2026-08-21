variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "project_name" {
  description = "Project name"
  type        = string
}

variable "vnet_address_space" {
  description = "Address space for VNet"
  type        = list(string)
}

variable "subnets" {
  description = "Subnet configurations"
  type = map(object({
    address_prefixes                   = list(string)
    service_endpoints                  = optional(list(string))
    private_endpoint_network_policies  = optional(string)
  }))
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
}