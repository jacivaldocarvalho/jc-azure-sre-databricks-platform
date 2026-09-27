variable "resource_group_id" {
  description = "ID of the project Resource Group"
  type        = string
}

variable "data_lake_storage_account_id" {
  description = "ID of the Data Lake Storage Account"
  type        = string
}

variable "databricks_managed_identity_principal_id" {
  description = "Principal ID of the Managed Identity used by Databricks"
  type        = string
}

variable "devops_principal_id" {
  description = "Principal ID of the Azure DevOps Service Principal (optional)"
  type        = string
  default     = ""
}

variable "openai_account_id" {
  description = "ID of the Azure OpenAI account. Empty to skip the assignment."
  type        = string
  default     = ""
}