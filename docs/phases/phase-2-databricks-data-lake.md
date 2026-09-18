# Phase 2 — Databricks and Data Lake

**Status:** Completed
**Duration:** Multi-iteration (three corrective cycles)
**Dependencies:** Phase 1 (Base Network)

---

## Objective

Provision the Databricks Workspace with VNet Injection and the Azure Data Lake Storage Gen2 that will host raw and processed data. This phase establishes the platform foundation for data engineering, ready to support:

- Notebook development and cluster execution
- Delta Lake tables on ADLS Gen2
- Unity Catalog (deferred to a later phase)
- Secure, private connectivity between compute and storage

---

## Context

### Why VNet Injection

Two deployment modes exist for Databricks:

| Mode | Characteristics | Trade-off |
|------|-----------------|-----------|
| Default (no VNet Injection) | Databricks manages its own VNet | Simple, no custom network control |
| VNet Injection | Databricks uses your VNet and subnets | Full control, private endpoints, custom NSG |

**Decision:** VNet Injection. It aligns with the SRE/DevOps goals of the project (network control, security, observability) and is required for integration with private endpoints and custom NSG rules.

### Two Subnets Requirement

VNet Injection requires two dedicated subnets:

- **Public subnet** — hosts the cluster VMs (delegated to `Microsoft.Databricks/workspaces`)
- **Private subnet** — hosts internal containers (also delegated)

The `databricks` subnet (10.0.1.0/24) was already planned in Phase 1. A new `databricks_private` subnet (10.0.6.0/24) was added in this phase.

### Databricks SKU

| SKU | Features | Cost |
|-----|----------|------|
| Standard | Basic | Lower |
| Premium | Unity Catalog, RBAC, IP access lists, cluster policies | Higher |

**Decision:** Premium. Required for Unity Catalog (aligned with the professional certification focus) and for advanced security features planned in later phases.

### Secure Cluster Connectivity (SCC)

SCC (also called "No Public IP") ensures workers have no public IP and communicate with the control plane through a secure tunnel. This is the modern recommended mode and became a requirement when using `NoAzureDatabricksRules`.

**Decision:** Enable SCC (`no_public_ip = true`) after resolving the NSG conflict (see Lessons Learned).

---

## Implementation

### 1. Databricks Module

Created `terraform/modules/databricks/` with:

- `main.tf` — `azurerm_databricks_workspace` with VNet Injection, SCC, and `NoAzureDatabricksRules`
- `variables.tf` — input contract (VNet ID, subnet names, NSG association IDs, storage account)
- `outputs.tf` — workspace ID, URL, name

**Key configuration:**

```hcl
resource "azurerm_databricks_workspace" "main" {
  name                                  = "${var.environment}-${var.project_name}-dbw"
  resource_group_name                   = var.resource_group_name
  location                              = var.location
  sku                                   = "premium"
  managed_resource_group_name           = "${var.environment}-${var.project_name}-dbw-managed-rg"
  network_security_group_rules_required = "NoAzureDatabricksRules"

  custom_parameters {
    virtual_network_id                                   = var.vnet_id
    public_subnet_name                                   = var.public_subnet_name
    private_subnet_name                                  = var.private_subnet_name
    public_subnet_network_security_group_association_id  = var.public_subnet_nsg_association_id
    private_subnet_network_security_group_association_id = var.private_subnet_nsg_association_id
    no_public_ip                                         = true
    storage_account_name                                 = "${var.storage_account_name}dbw"
    storage_account_sku_name                             = "Standard_LRS"
  }

  tags = var.tags
}
```

**Important:** the DBFS storage account (`${var.storage_account_name}dbw`) is separate from the data lake storage account to avoid a naming collision. This was discovered during an early apply.

### 2. Data Lake Module

Created `terraform/modules/datalake/` with:

- `main.tf` — ADLS Gen2 storage account with HNS enabled and four containers
- `variables.tf` — input contract
- `outputs.tf` — storage account ID, name, primary DFS endpoint

**Containers:**

| Container | Purpose |
|-----------|---------|
| `raw` | Ingested data, unchanged |
| `processed` | Transformed and aggregated data |
| `notebooks` | Workspace notebooks (backup / Git sync) |
| `checkpoints` | Structured Streaming checkpoints |

**Why HNS:** Hierarchical Namespace enables directory-level operations, POSIX permissions, and is the foundation of ADLS Gen2. Delta Lake performs significantly better on HNS-enabled storage.

### 3. Network Adjustments

Two adjustments to the networking module were required:

1. **Delegation support:** the `subnets` variable now accepts an optional `delegation` field. A `dynamic` block adds the delegation only when specified.

2. **New private subnet:** `databricks_private` (10.0.6.0/24) added with delegation `Microsoft.Databricks/workspaces`.

### 4. NSG and Network Intent Policy Conflict Resolution

This was the most complex issue in the phase. Summary of the iterations:

**Attempt 1 — Default NSG with `DenyAllInbound`**

Failed: the Databricks Network Intent Policy conflicted with `DenyAllInbound`, blocking workspace creation.

**Attempt 2 — `NoAzureDatabricksRules` without SCC**

Failed: `NoAzureDatabricksRules` requires `no_public_ip = true`. Without SCC, the API rejects the request.

**Attempt 3 — `NoAzureDatabricksRules` with SCC**

Succeeded. The final configuration:

- `NoAzureDatabricksRules` in the workspace
- `no_public_ip = true` in custom_parameters
- NSG contains the required rules for Databricks internal communication
- `DenyAllInbound` restored (compatible with SCC)

**Required NSG rules for SCC mode:**

| Rule | Direction | Source | Destination | Ports |
|------|-----------|--------|-------------|-------|
| `AllowAzureLoadBalancerInbound` | Inbound | AzureLoadBalancer | * | * |
| `databricks-worker-to-worker-inbound` | Inbound | VirtualNetwork | VirtualNetwork | * |
| `databricks-worker-to-databricks-webapp` | Outbound | VirtualNetwork | AzureDatabricks | 443,3306,8443-8451 |
| `databricks-worker-to-sql` | Outbound | VirtualNetwork | Sql | 3306 |
| `databricks-worker-to-storage` | Outbound | VirtualNetwork | Storage | 443 |
| `databricks-worker-to-eventhub` | Outbound | VirtualNetwork | EventHub | 9093 |
| `DenyAllInbound` | Inbound | * | * | * |

### 5. Region Decision

The initial region was `eastus`, but the subscription policy `sys.regionrestriction` limits resources to five regions: `eastus`, `northcentralus`, `centralus`, `brazilsouth`, `spaincentral`.

**Decision:** `brazilsouth`. It was the region with the best combination of proximity and SKU availability for the project.

---

## Validation

```bash
# Databricks Workspace
az databricks workspace show \
  --resource-group dev-sredatabricks-rg \
  --name dev-sredatabricks-dbw \
  --query "{Name:name, Sku:sku.name, Url:workspaceUrl, State:provisioningState}" \
  -o table

# Storage Account (ADLS Gen2)
az storage account show \
  --name devsredata \
  --resource-group dev-sredatabricks-rg \
  --query "{Name:name, Kind:kind, IsHns:isHnsEnabled, State:provisioningState}" \
  -o table

# Containers
az storage container list \
  --account-name devsredata \
  --auth-mode login \
  --query "[].name" \
  -o table

# Required NSG rules
az network nsg rule list \
  --resource-group dev-sredatabricks-rg \
  --nsg-name dev-sredatabricks-nsg \
  --query "[].{Name:name, Priority:priority, Direction:direction, Access:access}" \
  -o table

# Outputs
cd terraform/environments/dev
terraform output
```

**Expected results:**

1. Databricks Workspace exists, SKU Premium, state `Succeeded`
2. Storage Account is ADLS Gen2 (`isHnsEnabled = true`)
3. Four containers exist: `raw`, `processed`, `notebooks`, `checkpoints`
4. NSG contains all required Databricks rules
5. Outputs include workspace URL and storage DFS endpoint

---

## Lessons Learned

### What worked well

- Splitting Databricks and Data Lake into separate modules kept concerns isolated
- Dynamic delegation in the networking module enabled reuse without duplication
- Using a separate DBFS storage account name (`{base}dbw`) avoided a collision discovered during apply

### Adjustments made

1. **Removed `blob_properties.versioning_enabled`** — incompatible with `is_hns_enabled = true`. The hierarchy and versioning are mutually exclusive on the same account. Documented as a permanent design decision.

2. **Separated DBFS storage account name** — the original configuration tried to reuse `devsredata` for both the data lake and the DBFS account, causing a name conflict. Fixed by appending `dbw` suffix.

3. **Adopted SCC + NoAzureDatabricksRules** — the most professional posture for a production-grade Databricks deployment. Trade-off: no NAT Gateway provisioned at this stage, so the cluster cannot reach the public internet (pip, Maven). This is documented as a known limitation of the current phase.

4. **Region moved to `brazilsouth`** — driven by the `sys.regionrestriction` policy of the Azure for Students subscription.

### What would be done differently

- The NSG conflict could have been anticipated by consulting the Databricks documentation on VNet Injection requirements before writing the NSG. The lesson: **always consult the managed service's networking requirements before applying restrictive defaults to its delegated subnets.**

---

## Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Databricks module | `terraform/modules/databricks/` | Workspace provisioning |
| Data Lake module | `terraform/modules/datalake/` | ADLS Gen2 + containers |
| Updated networking | `terraform/modules/networking/` | Delegation + private subnet |
| Updated env dev | `terraform/environments/dev/` | Wiring |
| Sample vars | `terraform/environments/dev/terraform.tfvars` | Region, storage account, subnets |

**Azure resources:**

| Resource | Name | Notes |
|----------|------|-------|
| Databricks Workspace | `dev-sredatabricks-dbw` | Premium, VNet Injection, SCC |
| Managed Resource Group | `dev-sredatabricks-dbw-managed-rg` | auto-created by Databricks |
| DBFS Storage Account | `devsredatadbw` | auto-created by Databricks |
| Data Lake Storage Account | `devsredata` | ADLS Gen2, HNS enabled |
| Containers | `raw`, `processed`, `notebooks`, `checkpoints` | private access |
| NSG Rules | 7 rules | see table above |

---

## Next Phase

[Phase 3 — Data Pipeline](phase-3-pipeline.md): implement the data ingestion, validation, transformation, and persistence pipeline.
