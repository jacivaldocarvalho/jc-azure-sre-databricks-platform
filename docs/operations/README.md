# Operations

Runbooks, procedures, and operational guidance for the JC-Azure SRE Databricks Platform.

---

## Purpose

This directory holds the operational knowledge required to run, maintain, and recover the platform. The intent is to reduce the dependency on tribal knowledge: any qualified operator should be able to perform the documented tasks without needing the original author.

This is a working document. As new operational scenarios are encountered, they are documented here.

---

## Structure

```
docs/operations/
├── README.md               # This file
└── (future runbooks will be added here)
```

Planned runbooks, to be added as the project progresses:

| Runbook | Target Phase | Description |
|---------|--------------|-------------|
| `rotate-credentials.md` | Phase 6 (current) | Rotate Service Principal and Key Vault secrets |
| `backup-and-restore.md` | Phase 9 | Back up and restore critical data |
| `incident-response.md` | Phase 5 | Response procedure for common incidents |
| `cost-review.md` | Phase 10 | Monthly cost review procedure |

---

## Day-to-Day Operations

### 1. Provision the Full Environment

```bash
cd ~/projetos/jc-azure-sre-databricks-platform
make terraform-init
make terraform-plan
make terraform-apply
```

Takes approximately 15 to 25 minutes, dominated by the Databricks Workspace creation.

### 2. Destroy the Environment

```bash
make terraform-destroy
```

Takes approximately 5 to 10 minutes.

**Note:** the Terraform state backend (`tfstate-rg` resource group and `tfstatejcsredatabricks` storage account) is **not** destroyed, as it is not managed by this Terraform configuration.

### 3. Run the Data Pipeline Locally

```bash
cd python
source .venv/bin/activate
python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
```

Takes 30 seconds to 2 minutes.

### 4. Run the Test Suite

```bash
cd python
source .venv/bin/activate
pytest tests/ -v
```

Takes approximately 15 to 25 seconds.

### 5. Clean Local Artifacts

```bash
cd python
rm -rf spark-warehouse .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

Removes Delta tables, Pytest cache, and Python bytecode.

---

## Post-Apply Checklist

Some resources were created manually or are not fully managed by Terraform. They must be recreated or verified after each `terraform destroy` + `terraform apply` cycle.

### Why manual

For speed of iteration and KQL query tuning, the Workbook and alert rules were created in the portal first. The migration to Terraform is planned for a future phase. Additionally, the Azure DevOps Service Principal scope change was applied manually since the SP was created outside of Terraform.

### Resources to recreate or verify

After `make terraform-apply`, follow these steps:

#### 1. Application Insights Secret in Key Vault

After the new Application Insights is provisioned by Terraform, populate the Key Vault with the new connection string:

```bash
cd terraform/environments/dev

# Get the connection string
terraform output -raw application_insights_connection_string > /tmp/ai-conn.txt

# Ensure no trailing newline
tr -d '\n' < /tmp/ai-conn.txt > /tmp/ai-conn-clean.txt

# Store in Key Vault
az keyvault secret set \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" \
  --file /tmp/ai-conn-clean.txt

# Clean up temporary files
rm /tmp/ai-conn.txt /tmp/ai-conn-clean.txt
```

If the secret already exists (soft-deleted from previous destroy), purge it first:

```bash
az keyvault secret delete \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" 2>/dev/null || true

az keyvault secret purge \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" 2>/dev/null || true
```

#### 2. Action Group

| Field | Value |
|-------|-------|
| Name | `sre-oncall` |
| Display name | `SRE On-Call` |
| Resource Group | `dev-sredatabricks-rg` |
| Notification type | Email |
| Email | the operator's address |

Location: **Monitor** → **Alerts** → **Action groups** → **Create**.

#### 3. Workbook

| Field | Value |
|-------|-------|
| Name | `Pipeline Overview` |
| Target | Application Insights `dev-sredatabricks-ai` |
| Save to | Shared Reports |

The workbook has five panels. The KQL queries for each panel are documented in `docs/phases/phase-5-observability.md`.

**Note:** For the freshness panel, use `tolong(valueMax)` before passing to `datetime_add()` to avoid the type error.

#### 4. Alert Rules

Create four alert rules against Application Insights `dev-sredatabricks-ai`:

| Name | Severity | Query filter |
|------|----------|--------------|
| `pipeline-failure` | 1 (Error) | Failures in the last 5 minutes |
| `pipeline-data-stale` | 1 (Error) | Freshness > 24 hours |
| `pipeline-low-volume` | 2 (Warning) | Volume < 1000 rows per hour |
| `pipeline-slow` | 2 (Warning) | P95 duration > 120 seconds |

All rules reference the `sre-oncall` action group.

The full KQL queries for each rule are documented in `docs/phases/phase-5-observability.md`.

#### 5. Verify Service Principal Scope

After recreating the environment, verify that the Azure DevOps Service Principal still has Contributor at the Resource Group scope:

```bash
SP_OID=$(az ad sp list --display-name "jc-sre-databricks-pipeline" --query "[0].id" -o tsv)

az role assignment list \
  --assignee "$SP_OID" \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**Expected:** Contributor at the Resource Group scope.

If the assignment is missing (e.g., after a fresh recreation of the Service Principal), recreate it:

```bash
az role assignment create \
  --assignee "$SP_OID" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg"
```

#### 6. Verify Managed Identity Role Assignments

The Terraform `security` module recreates the role assignments automatically. Verify:

```bash
# Databricks Managed Identity on Storage
az role assignment list \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg/providers/Microsoft.Storage/storageAccounts/devsredata" \
  --query "[].{Principal:principalId, Role:roleDefinitionName}" \
  -o table
```

**Expected:** one assignment with `Storage Blob Data Contributor`.

```bash
# Databricks Managed Identity on Key Vault
az role assignment list \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg/providers/Microsoft.KeyVault/vaults/dev-sredatabricks-kv" \
  --query "[].{Principal:principalId, Role:roleDefinitionName}" \
  -o table
```

**Expected:** two assignments (Key Vault Administrator for the user, Key Vault Secrets User for the Managed Identity).

---

## Security Auditing

The following checks should be performed periodically to maintain the security posture. See `docs/architecture/security-model.md` for the full model.

### Quarterly Audit

#### 1. Review role assignments

```bash
# All role assignments in the subscription
az role assignment list \
  --all \
  --query "[].{Principal:principalName, Type:principalType, Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**What to check:**
- No unexpected Service Principals have access
- No role assignments at the subscription scope other than the Owner
- The Azure DevOps SP has Contributor only at the Resource Group

#### 2. Review secrets and credentials

```bash
# List all secrets in Key Vault
az keyvault secret list \
  --vault-name dev-sredatabricks-kv \
  --query "[].{Name:name, Enabled:attributes.enabled, Expires:attributes.expires}" \
  -o table

# List all credentials (client secrets) of the Azure DevOps App Registration
az ad app credential list \
  --id f0fa3958-4d24-45d1-bdb4-e8af5f4d7147 \
  --query "[].{Name:displayName, EndDate:endDateTime}" \
  -o table
```

**What to check:**
- All secrets are actively used
- No secrets near expiration without a rotation plan
- No orphaned secrets

**Note:** the Azure DevOps App Registration uses OIDC, so it should have **no** client secrets. If any appear, investigate and revoke.

#### 3. Review the Managed Identity

```bash
# Confirm the Managed Identity exists and is assigned to the workspace
az identity show \
  --name dev-sredatabricks-dbw-mi \
  --resource-group dev-sredatabricks-rg \
  --query "{Name:name, ClientId:clientId, PrincipalId:principalId}" \
  -o table

# List all role assignments for the Managed Identity
MI_PRINCIPAL=$(az identity show --name dev-sredatabricks-dbw-mi --resource-group dev-sredatabricks-rg --query principalId -o tsv)

az role assignment list \
  --assignee "$MI_PRINCIPAL" \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**What to check:**
- Only the expected roles are present (Key Vault Secrets User, Storage Blob Data Contributor)
- No unexpected scope expansion

#### 4. Review the Key Vault access

```bash
az role assignment list \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg/providers/Microsoft.KeyVault/vaults/dev-sredatabricks-kv" \
  --query "[].{Principal:principalName, Type:principalType, Role:roleDefinitionName}" \
  -o table
```

**What to check:**
- Only the operator and the Databricks Managed Identity have access
- No Service Principals have access unless explicitly required

### Rotation Procedures

#### Rotating the Application Insights connection string

1. Recreate the Application Insights (or generate a new connection string):

```bash
# This is normally done by terraform destroy + apply on the monitoring module
cd terraform/environments/dev
terraform apply -replace=module.monitoring.azurerm_application_insights.main
```

2. Update the Key Vault secret:

```bash
terraform output -raw application_insights_connection_string > /tmp/ai-conn.txt
tr -d '\n' < /tmp/ai-conn.txt > /tmp/ai-conn-clean.txt

az keyvault secret set \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" \
  --file /tmp/ai-conn-clean.txt

rm /tmp/ai-conn.txt /tmp/ai-conn-clean.txt
```

3. Restart any process that holds the connection string in memory (the local pipeline will pick it up on the next run).

#### Rotating the Azure CLI session

The Azure CLI session is refreshed automatically on `az login`. To force a refresh:

```bash
az logout
az login
az account set --subscription <SUBSCRIPTION_ID>
```

The session is used by both Terraform and the Python pipeline in local development.

#### Revoking the Azure DevOps Federated Credential

If the Service Connection is compromised or needs recreation:

```bash
# List federated credentials
az ad app federated-credential list --id f0fa3958-4d24-45d1-bdb4-e8af5f4d7147 -o table

# Delete a specific credential
az ad app federated-credential delete \
  --id f0fa3958-4d24-45d1-bdb4-e8af5f4d7147 \
  --federated-credential-id <credential-name>
```

Recreate it with the exact issuer and subject that Azure DevOps generates (see `docs/phases/phase-4-cicd.md`).

---

## Routine Checks

### Weekly

- Review the Azure Portal for unexpected resources
- Check the subscription credit balance
- Review the `Pipeline Overview` workbook for anomalies
- Confirm no alerts are firing

### Before Each Session

- Confirm the correct subscription is active: `az account show`
- Confirm the `.env` file is present and populated
- Confirm the `AZURE_USE_CLI=true` variable is set for local development

### After Each Session

- If resources were provisioned for the session, destroy them (`make terraform-destroy`)
- Verify the Terraform state is consistent: `terraform plan` should report no changes

---

## Escalation and Support

This is a solo portfolio project. There is no on-call rotation. The escalation path is:

1. Consult this documentation
2. Consult the phase documentation in `../phases/`
3. Consult the architecture ADRs in `../architecture/`
4. Consult the troubleshooting guides in `../troubleshooting/`
5. Consult the original cloud provider documentation (Microsoft, Databricks, Terraform)

---

## Related Documentation

- [Phases](../phases/) — what was implemented
- [Architecture](../architecture/) — architectural decisions
- [Security Model](../architecture/security-model.md) — full security posture
- [Troubleshooting](../troubleshooting/) — problem resolution guides
- [Conventions](../conventions.md) — project standards
