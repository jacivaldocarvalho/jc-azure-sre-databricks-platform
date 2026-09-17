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

variable "vnet_id" {
  description = "ID of the VNet"
  type        = string
}

variable "public_subnet_name" {
  description = "Name of the public subnet for Databricks"
  type        = string
}

variable "private_subnet_name" {
  description = "Name of the private subnet for Databricks"
  type        = string
}

variable "public_subnet_nsg_association_id" {
  description = "ID of the NSG association for the public subnet"
  type        = string
}

variable "private_subnet_nsg_association_id" {
  description = "ID of the NSG association for the private subnet"
  type        = string
}

variable "storage_account_name" {
  description = "Name of the storage account for Databricks workspace storage"
  type        = string
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
}