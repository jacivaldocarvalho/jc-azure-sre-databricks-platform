terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.0"
    }
  }
}

# =============================================================================
# AKS Cluster
# =============================================================================

resource "azurerm_kubernetes_cluster" "main" {
  name                = "${var.environment}-${var.project_name}-aks"
  location            = var.location
  resource_group_name = var.resource_group_name

  dns_prefix          = "${var.environment}-${var.project_name}"
  kubernetes_version  = var.kubernetes_version
  sku_tier            = "Free"

  # Use the existing AKS subnet
  default_node_pool {
    name                 = "system"
    vm_size              = var.node_vm_size
    vnet_subnet_id       = var.subnet_id
    os_disk_size_gb      = 30
    os_disk_type         = "Managed"
    type                 = "VirtualMachineScaleSets"
    enable_auto_scaling  = true
    min_count            = var.node_min_count
    max_count            = var.node_max_count

    # Keep nodes clean and reduce cost
    only_critical_addons_enabled = true

    tags = var.tags
  }

  # System-assigned managed identity
  identity {
    type = "SystemAssigned"
  }

  # Network profile: Azure CNI with Calico network policy
  network_profile {
    network_plugin    = "azure"
    network_policy    = "calico"
    load_balancer_sku = "standard"
    outbound_type     = "loadBalancer"
  }

  # RBAC and Azure AD integration
  role_based_access_control_enabled = true

  # Disable the default monitoring addon (we deploy Prometheus via Helm)
  # oms_agent is not enabled here

  tags = var.tags

  lifecycle {
    ignore_changes = [
      # Prevent recreation when Kubernetes version is auto-upgraded
      kubernetes_version,
    ]
  }
}

# =============================================================================
# User node pool for application workloads
# =============================================================================

resource "azurerm_kubernetes_cluster_node_pool" "workloads" {
  name                  = "workloads"
  kubernetes_cluster_id = azurerm_kubernetes_cluster.main.id
  vm_size               = var.node_vm_size
  vnet_subnet_id        = var.subnet_id
  os_disk_size_gb       = 30
  os_disk_type          = "Managed"
  mode                  = "User"
  enable_auto_scaling   = true
  min_count             = var.workload_node_min_count
  max_count             = var.workload_node_max_count

  node_labels = {
    "workload" = "application"
  }

  tags = var.tags
}

# =============================================================================
# Role assignments for AKS to pull images and read secrets
# =============================================================================

# Allow the AKS kubelet identity to pull images from the ACR
resource "azurerm_role_assignment" "aks_acr_pull" {
  count = var.acr_id != "" ? 1 : 0

  scope                = var.acr_id
  role_definition_name = "AcrPull"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id

  description = "Allow AKS to pull images from the project ACR"
}

# Allow the AKS managed identity to read secrets from Key Vault
resource "azurerm_role_assignment" "aks_keyvault_reader" {
  count = var.key_vault_id != "" ? 1 : 0

  scope                = var.key_vault_id
  role_definition_name = "Key Vault Secrets User"
  principal_id         = azurerm_kubernetes_cluster.main.kubelet_identity[0].object_id

  description = "Allow AKS workloads to read secrets from Key Vault"
}
