# Runbook — Recover a Key Vault Secret

Procedure for recovering a secret that was deleted from the Key Vault,
either accidentally or as part of a failed operation.

---

## When to Use This Runbook

Use this runbook when:

- A secret was accidentally deleted from the Key Vault
- A `terraform destroy` removed the Key Vault, and the secret needs to
  be re-populated after `terraform apply`
- The application cannot resolve a secret from the Key Vault
- The soft-delete retention window is about to expire

**Do not use this runbook** for secret rotation. Rotation is a planned
operation, not a recovery. See the rotation procedures in the operations
README.

---

## Prerequisites

| Requirement | How to Verify |
|-------------|---------------|
| Azure CLI authenticated | `az account show` |
| Access to the Key Vault | `az keyvault show --name dev-sredatabricks-kv` |
| `Key Vault Administrator` or `Key Vault Secrets Officer` role | `az role assignment list --assignee $(az ad signed-in-user show --query id -o tsv) --scope <keyvault-id>` |

**Key Vault information:**

| Field | Value |
|-------|-------|
| Name | `dev-sredatabricks-kv` |
| Resource Group | `dev-sredatabricks-rg` |
| Soft delete retention | 7 days |
| Secrets | `applicationinsights-connection-string` |

---

## Recovery Decision Tree

```
              ┌─────────────────────────────────────┐
              │  What is the situation?             │
              └──────────────────┬──────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ Secret     │    │ Key Vault  │    │ Secret     │
       │ deleted    │    │ destroyed  │    │ not found  │
       │ (soft)     │    │ (destroy)  │    │ (unknown)  │
       └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
             │                 │                 │
             ▼                 ▼                 ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
      │ Procedure A: │  │ Procedure B: │  │ Procedure C: │
      │ Undelete     │  │ Re-provision │  │ Investigate  │
      │ secret       │  │ Key Vault +  │  │ and recreate │
      │              │  │ re-populate  │  │              │
      └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Procedure A — Undelete a Soft-Deleted Secret

**Scenario:** the secret was recently deleted, and the soft-delete retention (7 days) has not expired.

### Step 1: List deleted secrets

```bash
az keyvault secret list-deleted \
  --vault-name dev-sredatabricks-kv \
  --query "[].{Name:name, DeletedDate:attributes.deletedDate, ScheduledPurgeDate:attributes.scheduledPurgeDate}" \
  -o table
```

**What to look for:**

- `ScheduledPurgeDate` is the date when the secret will be permanently deleted
- If the secret appears and the date has not passed, recover it (Step 2)
- If the secret does not appear, use Procedure B or C

### Step 2: Recover the secret

```bash
az keyvault secret recover \
  --vault-name dev-sredatabricks-kv \
  --name applicationinsights-connection-string
```

**Expected output:** the recovered secret metadata, including the new `id`.

### Step 3: Verify the recovery

```bash
az keyvault secret show \
  --vault-name dev-sredatabricks-kv \
  --name applicationinsights-connection-string \
  --query "{Name:name, Enabled:attributes.enabled, Created:attributes.created}" \
  -o table
```

**Expected:** the secret appears with `Enabled: true`.

### Step 4: Verify the pipeline can read it

```bash
cd ~/projetos/jc-azure-sre-databricks-platform/python
source .venv/bin/activate

python -c "
from azure.identity import AzureCliCredential
from azure.keyvault.secrets import SecretClient

credential = AzureCliCredential()
client = SecretClient(
    vault_url='https://dev-sredatabricks-kv.vault.azure.net/',
    credential=credential,
)
secret = client.get_secret('applicationinsights-connection-string')
print('OK:', secret.value[:50])
"
```

**Expected:** the first 50 characters of the connection string.

---

## Procedure B — Re-Provision the Key Vault and Re-Populate the Secret

**Scenario:** the Key Vault was destroyed (e.g., by `terraform destroy`), or the soft-delete retention expired.

### Step 1: Provision the Key Vault via Terraform

```bash
cd ~/projetos/jc-azure-sre-databricks-platform
make terraform-init
make terraform-plan
make terraform-apply
```

This recreates the Key Vault, the Managed Identity, and the role assignments.

**Prerequisite:** the rest of the environment must also be present
(otherwise, `terraform apply` will recreate everything).

### Step 2: Get the new connection string

After the Application Insights is provisioned (or re-provisioned), get
the new connection string:

```bash
cd terraform/environments/dev
terraform output -raw application_insights_connection_string
```

### Step 3: Populate the Key Vault with the secret

```bash
cd terraform/environments/dev

# Save to file to avoid copy-paste issues
terraform output -raw application_insights_connection_string > /tmp/ai-conn.txt

# Remove trailing newline
tr -d '\n' < /tmp/ai-conn.txt > /tmp/ai-conn-clean.txt

# Upload to Key Vault
az keyvault secret set \
  --vault-name dev-sredatabricks-kv \
  --name applicationinsights-connection-string \
  --file /tmp/ai-conn-clean.txt

# Clean up
rm /tmp/ai-conn.txt /tmp/ai-conn-clean.txt
```

### Step 4: Verify

```bash
az keyvault secret show \
  --vault-name dev-sredatabricks-kv \
  --name applicationinsights-connection-string \
  --query "{Name:name, Enabled:attributes.enabled}" \
  -o table
```

---

## Procedure C — Investigate and Recreate an Unknown Secret

**Scenario:** the secret is missing, and it is not clear why.

### Step 1: Check the deleted secrets

Follow Procedure A, Step 1.

### Step 2: Check if the Key Vault exists

```bash
az keyvault show --name dev-sredatabricks-kv \
  --query "{Name:name, Location:location, State:properties.provisioningState}" \
  -o table
```

If the Key Vault does not exist, follow Procedure B.

### Step 3: Check if the secret ever existed

If the secret is not in the deleted secrets list and the Key Vault exists,
the secret was never created (or was purged). Follow Procedure B, Steps 2-4.

### Step 4: Document the incident

Add an entry to `docs/operations/dr-test-log.md` describing the incident
and the recovery.

---

## Common Scenarios

| Scenario | Procedure | Estimated time |
|----------|-----------|----------------|
| Secret accidentally deleted (within 7 days) | A | 5 minutes |
| Secret deleted but Key Vault intact (past 7 days) | B (steps 2-4) | 10 minutes |
| Key Vault destroyed by `terraform destroy` | B | 20 minutes |
| Secret missing, unknown cause | C | Varies |

---

## Prevention

- **Soft delete** is enabled on the Key Vault (7 days retention).
- **Purge protection** could be enabled to prevent permanent deletion,
  but is not currently enabled (would require a paid tier or a change
  to the Terraform configuration).
- **Never manually delete secrets.** Use the rotation procedure instead.
- **Document secrets** in `.env.example` (without values) so future
  operators know what should exist.

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