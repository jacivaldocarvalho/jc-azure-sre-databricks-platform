# Phase 6 — Security

**Status:** Completed
**Duration:** Multi-iteration (Key Vault provisioning, legacy cleanup, RBAC granularity, security model documentation)
**Dependencies:** Phase 5 (Observability)

---

## Objective

Establish a coherent security posture for the project by:

- Centralizing secrets in Azure Key Vault with RBAC-based access
- Eliminating orphaned credentials and legacy service principals
- Applying least privilege to every identity
- Providing a Managed Identity for the Databricks workspace
- Documenting the security model as code and as reference

The result is a project where every credential has a purpose, every identity has a defined scope, and every secret is managed through a proper lifecycle.

---

## Context

### State before Phase 6

Before this phase, the project had:

| Component | Security Posture |
|-----------|------------------|
| Application Insights connection string | Stored in `.env` (plain text on developer machine) |
| Service Principal (legacy) | Contributor at subscription scope, with an active client secret |
| Databricks Managed Identity | Not provisioned |
| Key Vault | Not provisioned |
| ADLS access | Not explicitly assigned to any identity |
| Secrets in CI/CD | Mitigated by OIDC in Phase 4 |

### Gaps identified

| ID | Gap | Risk |
|----|-----|------|
| G1 | Legacy Service Principal with Contributor at subscription | High — full access to subscription |
| G2 | Connection string in `.env` | Medium — leaks if the file is exposed |
| G3 | No Key Vault | Medium — no centralized secret storage |
| G4 | No Managed Identity for Databricks | Medium — no path for programmatic ADLS access |
| G5 | No formal RBAC model | Medium — permissions accumulate over time |
| G6 | No security documentation | Low — decisions become tribal knowledge |

---

## Implementation

### 1. Key Vault with RBAC authorization

Created `terraform/modules/keyvault/` with:

- `azurerm_key_vault` — Standard tier, RBAC-based access, soft delete enabled (7 days)
- `azurerm_user_assigned_identity` — dedicated Managed Identity for Databricks
- Role assignments: Key Vault Administrator (current user) and Key Vault Secrets User (Databricks Managed Identity)

```
                       ┌─────────────────────────┐
                       │  Key Vault              │
                       │  dev-sredatabricks-kv   │
                       │  (Standard, RBAC)       │
                       └────────────┬────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │                               │
                    ▼                               ▼
       ┌────────────────────────┐     ┌────────────────────────────┐
       │  Operator (user)       │     │  Databricks Managed        │
       │  Key Vault             │     │  Identity                  │
       │  Administrator         │     │  Key Vault Secrets User    │
       └────────────────────────┘     └────────────────────────────┘
```

### 2. Secret migration

The Application Insights connection string was migrated from `.env` to Key Vault as a secret named `applicationinsights-connection-string`.

The pipeline Python was updated to resolve the connection string in order:

1. `APPLICATIONINSIGHTS_CONNECTION_STRING` environment variable (for debugging)
2. Azure Key Vault (default in production)

```
                 Pipeline startup
                        │
                        ▼
             ┌───────────────────────┐
             │  Env var set?         │
             └───────┬───────────────┘
                     │
              Yes ───┴─── No
               │           │
               ▼           ▼
        ┌───────────┐  ┌──────────────────┐
        │ Use env   │  │ Read from        │
        │ var       │  │ Key Vault        │
        └───────────┘  └────────┬─────────┘
                                │
                                ▼
                        ┌──────────────────┐
                        │ Configure OTel   │
                        │ exporter         │
                        └──────────────────┘
```

### 3. Authentication model for the pipeline

The pipeline uses a credential that depends on the environment:

| Environment | Credential | Trigger |
|-------------|------------|---------|
| Local development | `AzureCliCredential` | `AZURE_USE_CLI=true` |
| Azure deployment | `DefaultAzureCredential` | Variable unset |

This avoids interference from environment variables that `DefaultAzureCredential` would otherwise pick up first.

### 4. Cleanup of legacy Service Principal

A Service Principal (`58ce9313-...`) with Contributor at subscription scope was identified and removed. It was created in Phase 1/2 when the project used credentials-based authentication. Since Phase 4 (OIDC), it was no longer used.

Actions taken:

1. Revoked the client secret (`rbac`)
2. Removed the Contributor role assignment at subscription scope
3. Deleted the App Registration (and the associated Service Principal)

Verification confirmed that the App Registration no longer exists and has no remaining role assignments.

### 5. RBAC granularity

Created `terraform/modules/security/` with:

- `azurerm_role_assignment.databricks_storage` — grants `Storage Blob Data Contributor` to the Databricks Managed Identity on the Data Lake Storage Account
- `azurerm_role_assignment.devops_contributor_rg` — grants `Contributor` to the Azure DevOps Service Principal at the Resource Group scope (optional, controlled by a variable)

The Azure DevOps Service Principal scope was reduced manually from Subscription to Resource Group.

```
        Before Phase 6                          After Phase 6
        ──────────────                          ─────────────

        Subscription                            Subscription
       ┌─────────────────────┐                 ┌─────────────────────┐
       │  SP (DevOps)        │                 │                     │
       │  Contributor        │                 │  (no access)        │
       │  (subscription)     │                 │                     │
       └─────────────────────┘                 └──────────┬──────────┘
                                                         │
                                                         ▼
                                              ┌─────────────────────┐
                                              │  Resource Group     │
                                              │  dev-sredatabricks  │
                                              │  ┌───────────────┐  │
                                              │  │ SP (DevOps)   │  │
                                              │  │ Contributor   │  │
                                              │  └───────────────┘  │
                                              └─────────────────────┘
```

### 6. Managed Identity on ADLS

The Databricks Managed Identity now has `Storage Blob Data Contributor` on the Data Lake Storage Account. This allows the Databricks workspace to read and write to the containers without using shared account keys.

| Container | Access |
|-----------|--------|
| `raw` | Read, write |
| `processed` | Read, write |
| `notebooks` | Read, write |
| `checkpoints` | Read, write |

---

## Validation

### Key Vault

```bash
az keyvault show \
  --name dev-sredatabricks-kv \
  --query "{Name:name, RBAC:properties.enableRbacAuthorization}" \
  -o table
```

**Expected:** `RBAC: True`.

```bash
az keyvault secret list \
  --vault-name dev-sredatabricks-kv \
  --query "[].{Name:name, Enabled:attributes.enabled}" \
  -o table
```

**Expected:** `applicationinsights-connection-string` listed.

### Managed Identity on ADLS

```bash
az role assignment list \
  --scope "/subscriptions/.../storageAccounts/devsredata" \
  --query "[].{Principal:principalId, Role:roleDefinitionName}" \
  -o table
```

**Expected:** Databricks Managed Identity with `Storage Blob Data Contributor`.

### Azure DevOps Service Principal

```bash
az role assignment list \
  --assignee "<SP_OID>" \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**Expected:** `Contributor` at the Resource Group scope only.

### Pipeline execution

The pipeline runs successfully and the log shows:

```
INFO | src.utils.metrics | Loaded connection string from Key Vault.
INFO | src.utils.metrics | Azure Monitor metrics exporter configured.
INFO | src.utils.metrics | Metrics provider initialized.
```

### Legacy Service Principal

```bash
az ad app show --id 58ce9313-b5df-4624-80ab-80dd16ab73cf
```

**Expected:** `does not exist`.

---

## Lessons Learned

### What worked well

- **Key Vault with RBAC authorization** (instead of access policies) integrates cleanly with role assignments and supports Managed Identity without additional configuration.
- **`AZURE_USE_CLI` variable** made the credential selection explicit in local development, avoiding the confusing fallback behavior of `DefaultAzureCredential`.
- **Separation of concerns** between the `keyvault` module (secret storage) and the `security` module (role assignments) keeps each module focused and testable.

### Adjustments made

1. **`EnvironmentCredential` interference:** the `.env` contained `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` for a legacy Service Principal. Because `DefaultAzureCredential` tries `EnvironmentCredential` first, the pipeline authenticated as the legacy SP (which had no Key Vault access). Fixed by:
   - Removing the legacy credentials from `.env`
   - Adding `AZURE_USE_CLI=true` to force `AzureCliCredential`
   - Documenting the pattern in the code

2. **Secret in `.env` was truncated:** when copying the connection string from the terminal, it was truncated with embedded newlines. Fixed by using `az keyvault secret set --file` with a cleaned file (`tr -d '\n'`).

3. **`DefaultAzureCredential` order matters:** the default credential chain tries environment first, then Managed Identity, then VS Code, then CLI. This is designed for production but can be surprising in local development with leftover env vars.

### What would be done differently

- **Start with Key Vault from Phase 1** instead of Phase 6. Every secret (storage keys, DBFS tokens) should have been in Key Vault from the start. Retrofitting is more work than starting clean.
- **Avoid Service Principal with secret from the beginning.** Use OIDC (Workload Identity Federation) from day one for CI/CD.

---

## Artifacts

### Code

| Artifact | Path | Purpose |
|----------|------|---------|
| Key Vault module | `terraform/modules/keyvault/` | Key Vault + Managed Identity |
| Security module | `terraform/modules/security/` | Role assignments |
| Metrics module | `python/src/utils/metrics.py` | Key Vault resolution logic |

### Azure resources (Terraform-managed)

| Resource | Name |
|----------|------|
| Key Vault | `dev-sredatabricks-kv` |
| User-Assigned Managed Identity | `dev-sredatabricks-dbw-mi` |
| Role assignment (Key Vault) | Managed Identity → Key Vault Secrets User |
| Role assignment (Storage) | Managed Identity → Storage Blob Data Contributor |

### Azure resources (manually modified)

| Resource | Change |
|----------|--------|
| Azure DevOps SP scope | Subscription → Resource Group |

### Azure resources (removed)

| Resource | Action |
|----------|--------|
| App Registration `58ce9313-...` | Deleted |
| Client secret `rbac` | Revoked |
| Role assignment (subscription) | Removed |

---

## Next Phase

[Phase 7 — AI Integration](../phases/phase-7-ai.md): integrate Azure OpenAI and AI Foundry with the data pipeline.
