# Phase 1 — Base Network

**Status:** Completed
**Duration:** Initial Azure provisioning
**Dependencies:** Phase 0 (Foundation)

---

## Objective

Provision the foundational network infrastructure in Azure that will host all subsequent services (Databricks, AKS, monitoring, private endpoints). This phase establishes:

- A secure, segmented virtual network
- A restrictive network security group
- A remote backend for Terraform state
- A modular Terraform structure that can evolve independently

---

## Context

Before provisioning compute or platform services, the network must exist. Databricks with VNet Injection requires dedicated subnets with delegation. AKS requires its own subnet with appropriate service endpoints. Data and monitoring services need isolated segments.

Additionally, storing Terraform state locally is not viable for a professional project. A remote backend provides:

- Shared state across team members (future)
- State locking to prevent concurrent modifications
- Durability and backup
- Audit trail of infrastructure changes

### Architectural Decision: Network Topology

Three options were considered:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| A — Single VNet | One VNet, all subnets together | Simple, less secure |
| B — Hub-Spoke | Central hub with peering to spokes | Complex, more secure, production-grade |
| C — Single VNet with Private Endpoints | One VNet, segmented, PaaS via private endpoints | Balanced |

**Decision:** Option C. It provides adequate segmentation for the project scope, supports private endpoints (security best practice), and avoids the complexity of hub-spoke networking that would be over-engineering at this stage.

### Subnet Allocation

| Subnet | CIDR | Purpose |
|--------|------|---------|
| databricks | 10.0.1.0/24 | Databricks public subnet (delegated) |
| aks | 10.0.2.0/24 | AKS cluster nodes (future) |
| data | 10.0.3.0/24 | Data services (service endpoints) |
| monitoring | 10.0.4.0/24 | Prometheus and Grafana (future) |
| private_endpoints | 10.0.5.0/24 | Private endpoints for PaaS |
| databricks_private | 10.0.6.0/24 | Databricks private subnet (delegated) — added in Phase 2 |

---

## Implementation

### 1. Terraform Remote Backend

Created a dedicated Resource Group (`tfstate-rg`) and Storage Account (`tfstatejcsredatabricks`) with a container `tfstate` to hold the Terraform state files.

**Backend configuration:**

```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "tfstate-rg"
    storage_account_name = "tfstatejcsredatabricks"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}
```

**Why this matters:** state is stored outside the code repository, with versioning and durability provided by Azure Storage.

### 2. Networking Module

Created `terraform/modules/networking/` with:

- `main.tf` — VNet, subnets, NSG, NSG-subnet associations
- `variables.tf` — input contract
- `outputs.tf` — VNet ID, subnet IDs/names, NSG ID

The module accepts a `subnets` map and iterates over it using `for_each`. This allows adding new subnets without duplicating resource blocks.

**Dynamic delegation:** the module supports optional subnet delegation via a `dynamic` block, needed for Databricks VNet Injection.

### 3. Resource Naming and Tagging

All resources follow the project convention:

- Resource Group: `dev-sredatabricks-rg`
- VNet: `dev-sredatabricks-vnet`
- Subnets: `dev-sredatabricks-{name}-subnet`
- NSG: `dev-sredatabricks-nsg`

Tags applied to all resources:

```hcl
tags = {
  Environment = "dev"
  Project     = "SRE-Databricks"
  ManagedBy   = "Terraform"
}
```

### 4. Network Security Group

Initial configuration included:

- `AllowAzureLoadBalancerInbound` — required for Azure Load Balancer health probes
- `DenyAllInbound` — restrictive default posture

**Note:** the `DenyAllInbound` rule was later removed in Phase 2 due to a conflict with the Databricks Network Intent Policy. This is documented in the Phase 2 lesson learned.

---

## Validation

After applying the Terraform configuration:

```bash
# Resource Group
az group show --name dev-sredatabricks-rg -o table

# VNet and subnets
az network vnet show \
  --resource-group dev-sredatabricks-rg \
  --name dev-sredatabricks-vnet \
  --query "{Name:name, AddressSpace:addressSpace.addressPrefixes, Subnets:subnets[*].{Name:name, Prefix:addressPrefix}}" \
  -o table

# NSG
az network nsg show \
  --resource-group dev-sredatabricks-rg \
  --name dev-sredatabricks-nsg \
  --query "{Name:name, Rules:securityRules[*].{Name:name, Priority:priority, Direction:direction, Access:access}}" \
  -o table

# NSG associations
az network vnet subnet list \
  --resource-group dev-sredatabricks-rg \
  --vnet-name dev-sredatabricks-vnet \
  --query "[].{Subnet:name, NSG:networkSecurityGroup.id}" \
  -o table

# Remote backend
az storage blob show \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --name dev.terraform.tfstate \
  --auth-mode login \
  --query "{Name:name, Size:properties.contentLength, Modified:properties.lastModified}" \
  -o table
```

**Expected results:**

1. Resource Group, VNet, and NSG exist
2. All planned subnets are present with correct CIDRs
3. NSG is associated with each subnet
4. State file exists in the remote backend

---

## Lessons Learned

### What worked well

- Modular Terraform from the start avoided a monolithic `main.tf`
- The `for_each` pattern on subnets makes adding new subnets trivial
- Remote backend setup was done before any significant resource, avoiding a painful state migration later

### Adjustments made

- **Deprecated argument:** `private_endpoint_network_policies_enabled` is deprecated in AzureRM 4.x. It still works in 3.x but should be migrated. Tracked for a future maintenance window.
- **NSG default deny:** the initial `DenyAllInbound` rule conflicted with Databricks later. The lesson: when a subnet is delegated to a managed service, its NSG rules are subject to the service's own policy. Always verify before applying restrictive defaults.

---

## Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Networking module | `terraform/modules/networking/` | VNet, subnets, NSG |
| Dev environment | `terraform/environments/dev/` | Wiring of modules |
| Backend config | `terraform/environments/dev/backend.tf` | Remote state |
| Variables | `terraform/environments/dev/variables.tf` | Input contract |
| Sample vars | `terraform/environments/dev/terraform.tfvars.example` | Template |

**Azure resources:**

| Resource | Name | Notes |
|----------|------|-------|
| Resource Group | `dev-sredatabricks-rg` | main RG |
| Resource Group | `tfstate-rg` | remote backend (persistent) |
| Storage Account | `tfstatejcsredatabricks` | remote backend (persistent) |
| VNet | `dev-sredatabricks-vnet` | 10.0.0.0/16 |
| Subnets | 5 initial subnets | see table above |
| NSG | `dev-sredatabricks-nsg` | restrictive default |

---

## Next Phase

[Phase 2 — Databricks and Data Lake](phase-2-databricks-data-lake.md): provision the Databricks Workspace and Azure Data Lake Storage.
