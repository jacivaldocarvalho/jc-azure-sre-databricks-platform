# Runbook — Re-Provision the Environment

Procedure for rebuilding the entire Azure environment from scratch,
either after a `terraform destroy` or after a catastrophic failure.

---

## When to Use This Runbook

Use this runbook when:

- The Azure environment was intentionally destroyed (`terraform destroy`)
- A catastrophic failure requires rebuilding everything from scratch
- The state was lost and the environment needs to be recreated
- A developer wants to provision the environment for the first time

**Do not use this runbook** for a partial rebuild. If only one component
is broken, use the Terraform module-specific recovery.

---

## Prerequisites

| Requirement | How to Verify |
|-------------|---------------|
| Azure CLI authenticated | `az account show` |
| Terraform installed | `terraform version` |
| Access to the Terraform state backend | `az storage blob show --container-name tfstate --account-name tfstatejcsredatabricks --name dev.terraform.tfstate --auth-mode login` |
| The state is clean (either empty or matching the environment) | `terraform plan` |
| No other operation is running against the state | No active Terraform process |

**Backend information:**

| Field | Value |
|-------|-------|
| Resource Group | `tfstate-rg` |
| Storage Account | `tfstatejcsredatabricks` |
| Container | `tfstate` |
| Blob name | `dev.terraform.tfstate` |

---

## Procedure

### Step 1: Verify the state

Before provisioning, confirm that the state is in the expected condition:

```bash
cd ~/projetos/jc-azure-sre-databricks-platform/terraform/environments/dev
terraform init -reconfigure
terraform state list
```

**Expected:**

- If the environment is destroyed: the state should be **empty** (or contain only outputs).
- If the environment exists: the state should list all resources.

**If the state is inconsistent** (references resources that no longer
exist), use the [Recover Terraform State](recover-terraform-state.md)
runbook first.

### Step 2: Verify the Terraform variables

```bash
cat terraform.tfvars
```

**Expected:** the file should contain:

- `subscription_id`
- `environment`, `location`, `project_name`
- `storage_account_name`
- `subnets`, `vnet_address_space`
- `kubernetes_version`, `node_vm_size`
- `tags`

**If any variable is missing:** update the file before proceeding.

### Step 3: Init the Terraform environment

```bash
make terraform-init
```

Or directly:

```bash
cd terraform/environments/dev
terraform init
```

**Expected:** `Terraform has been successfully initialized!`

### Step 4: Plan the provisioning

```bash
make terraform-plan
```

Or directly:

```bash
terraform plan
```

**Expected:**

- If the environment is destroyed: `Plan: N to add, 0 to change, 0 to destroy`.
- If the environment exists: `No changes. Your infrastructure matches the configuration.`

**Review the plan carefully** before proceeding. Confirm that the
resources to be created match the expected environment.

### Step 5: Apply the provisioning

```bash
make terraform-apply
```

Or directly:

```bash
terraform apply
```

**Estimated time:** 15 to 25 minutes. Most of the time is spent on the
Databricks Workspace creation (~5 minutes) and the Application Insights
and Log Analytics provisioning (~3 minutes each).

**What Terraform creates:**

| Module | Resources |
|--------|-----------|
| Root | Resource Group |
| networking | VNet, 6 subnets, NSG, 6 NSG-subnet associations |
| datalake | Storage Account (ADLS Gen2), 4 containers |
| databricks | Databricks Workspace (Premium, VNet Injection, SCC) |
| monitoring | Azure Monitor Workspace, Log Analytics, Application Insights |
| keyvault | Key Vault, User-Assigned Managed Identity, 2 role assignments |
| security | Storage Blob Data Contributor for the Managed Identity |
| ai | (preserved, not applied) |
| aks | (preserved, not applied) |

### Step 6: Post-apply checklist

After `terraform apply` completes, execute the post-apply checklist
documented in `docs/operations/README.md`. It includes:

1. Populate the Application Insights secret in the Key Vault
2. Recreate the Action Group `sre-oncall`
3. Recreate the Workbook `Pipeline Overview`
4. Recreate the 4 alert rules
5. Verify the Service Principal scope
6. Verify the Managed Identity role assignments
7. Verify the AI and AKS configuration

**The post-apply checklist is not optional.** The Workbook, alert rules,
and Action Group are not managed by Terraform. Without them, the
observability of the pipeline is incomplete.

### Step 7: Verify the environment

```bash
# Resource Group
az group show --name dev-sredatabricks-rg -o table

# Databricks Workspace
az databricks workspace show \
  --resource-group dev-sredatabricks-rg \
  --name dev-sredatabricks-dbw \
  --query "{Name:name, Sku:sku.name, State:properties.provisioningState}" -o table

# Storage Account
az storage account show \
  --name devsredata \
  --resource-group dev-sredatabricks-rg \
  --query "{Name:name, Kind:kind, IsHns:isHnsEnabled}" -o table

# Key Vault
az keyvault show \
  --name dev-sredatabricks-kv \
  --query "{Name:name, RBAC:properties.enableRbacAuthorization}" -o table
```

**Expected:** all resources exist and are in `Succeeded` state.

### Step 8: Run the pipeline to verify

```bash
cd ~/projetos/jc-azure-sre-databricks-platform/python
source .venv/bin/activate
python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
```

**Expected:** the pipeline runs to completion. The log shows the
connection string was loaded from the Key Vault.

---

## Timing

| Phase | Estimated duration |
|-------|--------------------|
| Pre-checks (steps 1-2) | 2 minutes |
| Terraform init + plan (steps 3-4) | 3 minutes |
| Terraform apply (step 5) | 15-25 minutes |
| Post-apply checklist (step 6) | 10-15 minutes |
| Verification (steps 7-8) | 5 minutes |
| **Total** | **35-50 minutes** |

This exceeds the RTO of 4 hours only in the worst case. In practice,
the provisioning finishes in about 30 minutes.

---

## Common Issues

### Issue: `terraform apply` fails with `ResourceGroupNotFound`

**Cause:** the Resource Group was deleted outside of Terraform, but the state still references it.

**Fix:** see the [Recover Terraform State](recover-terraform-state.md) runbook.

### Issue: Databricks Workspace creation fails

**Cause:** the SKU is not available, or the quota is exhausted.

**Fix:** check `docs/architecture/adr-001-databricks-cluster-limitation.md`. The workspace itself should provision fine; the cluster cannot be created.

### Issue: Key Vault name already in use

**Cause:** the previous Key Vault is in soft-delete.

**Fix:** purge the soft-deleted vault:

```bash
az keyvault purge --name dev-sredatabricks-kv --location brazilsouth
```

Then re-run `terraform apply`.

---

## Prevention

- **Document the state.** The state should never be edited manually.
- **Back up the state.** Versioning is enabled on the backend (Phase 9).
- **Test the procedure.** Run the re-provisioning at least once per phase.
- **Keep the Terraform code up to date.** The current state should be
  reproducible from the code.

---

## Testing

This runbook was validated in Phase 9, Sub-etapa 9.4. See
`docs/operations/dr-test-log.md` for the test log.

---

## Related Documents

- [Disaster Recovery Reference](../disaster-recovery.md)
- [Phase 9 — Disaster Recovery](../../phases/phase-9-dr.md)
- [Operations README](../README.md)
- [Recover Terraform State](recover-terraform-state.md)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial runbook |
