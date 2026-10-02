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

variable "subnet_id" {
  description = "ID of the subnet for the AKS cluster nodes"
  type        = string
}

variable "kubernetes_version" {
  description = "Kubernetes version for the AKS cluster"
  type        = string
  default     = "1.30.0"
}

variable "node_vm_size" {
  description = "VM size for the AKS nodes"
  type        = string
  default     = "Standard_B2s"
}

variable "node_min_count" {
  description = "Minimum number of nodes in the system node pool"
  type        = number
  default     = 0
}

variable "node_max_count" {
  description = "Maximum number of nodes in the system node pool"
  type        = number
  default     = 2
}

variable "workload_node_min_count" {
  description = "Minimum number of nodes in the workload node pool"
  type        = number
  default     = 0
}

variable "workload_node_max_count" {
  description = "Maximum number of nodes in the workload node pool"
  type        = number
  default     = 3
}

variable "acr_id" {
  description = "ID of the Azure Container Registry. Empty to skip the role assignment."
  type        = string
  default     = ""
}

variable "key_vault_id" {
  description = "ID of the Key Vault. Empty to skip the role assignment."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Tags for resources"
  type        = map(string)
}
