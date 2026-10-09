# Runbook — Recover Terraform State

Procedure for recovering the Terraform state file from a corrupted,
deleted, or inconsistent condition.

---

## When to Use This Runbook

Use this runbook when any of the following occurs:

- The Terraform state file is corrupted (invalid JSON, unexpected content)
- The state file was accidentally deleted
- A `terraform apply` left the state inconsistent
- You need to roll back to a previous state (e.g., to recover from a bad change)
- The container holding the state was accidentally deleted

**Do not use this runbook** for routine operations. It is a recovery procedure, not a maintenance procedure.

---

## Prerequisites

| Requirement | How to Verify |
|-------------|---------------|
| Azure CLI authenticated | `az account show` |
| Terraform installed | `terraform version` |
| Access to the state backend | `az storage container show --name tfstate --account-name tfstatejcsredatabricks --auth-mode login` |
| Versioning enabled on the backend | `az storage account blob-service-properties show --account-name tfstatejcsredatabricks --resource-group tfstate-rg --query isVersioningEnabled` |

**Backend information:**

| Field | Value |
|-------|-------|
| Resource Group | `tfstate-rg` |
| Storage Account | `tfstatejcsredatabricks` |
| Container | `tfstate` |
| Blob name | `dev.terraform.tfstate` |
| Region | `eastus` (see Note below) |

**Note on the region:** the backend is in `eastus`, but the rest of the
infrastructure is in `brazilsouth`. This is a historical inconsistency
from Phase 0. The backend is accessed over HTTPS, so the cross-region
latency is negligible. Migrating the backend to `brazilsouth` is planned
for Phase 10 (governance).

---

## Recovery Decision Tree

Use this decision tree to identify which procedure to follow.

```
              ┌─────────────────────────────────────┐
              │  What is the problem?               │
              └──────────────────┬──────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ State file │    │ State file │    │ Container  │
       │ corrupted  │    │ deleted    │    │ deleted    │
       └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
             │                 │                 │
             ▼                 ▼                 ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
      │ Procedure A: │  │ Procedure B: │  │ Procedure C: │
      │ Roll back to │  │ Recover from │  │ Recover from │
      │ a previous   │  │ soft delete  │  │ container    │
      │ version      │  │              │  │ soft delete  │
      └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Procedure A — Roll Back to a Previous Version

**Scenario:** the state file exists but is corrupted or contains an
incorrect version of the infrastructure.

### Step 1: List the available versions

```bash
az storage blob list \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --auth-mode login \
  --include v \
  --query "[?name=='dev.terraform.tfstate'].{Version:versionId, Modified:properties.lastModified, Size:properties.contentLength}" \
  -o table
```

Or use the Makefile target:

```bash
make tfstate-versions
```

**What to look for:**

- **Modified**: the timestamp of each version. Sort mentally or pipe to `sort`.
- **Size**: the size in bytes. Typical sizes:
  - Empty state (no resources): ~180 bytes
  - Small infrastructure: 10-30 KB
  - Full infrastructure: 70-80 KB
- **Version**: the `versionId` (a timestamp string) used to reference the version.

### Step 2: Identify the target version

Choose the version based on:

1. **Timestamp**: pick a version from a moment when the state was known-good
2. **Size**: a size that matches the expected infrastructure
3. **Context**: the phase documentation (in `docs/phases/`) tells you what resources should be in the state at each moment

**Example:** to restore the state from before a recent destructive change, pick the version that immediately precedes the change.

### Step 3: Download the current state (backup)

Before modifying, save a copy of the current state:

```bash
mkdir -p /tmp/tfstate-backup
az storage blob download \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --name dev.terraform.tfstate \
  --file /tmp/tfstate-backup/dev.terraform.tfstate.current \
  --auth-mode login
```

**Why:** if the rollback makes things worse, you can restore the current state.

### Step 4: Download the target version

```bash
# Replace <VERSION_ID> with the version to restore
az storage blob download \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --name dev.terraform.tfstate \
  --version-id <VERSION_ID> \
  --file /tmp/tfstate-backup/dev.terraform.tfstate.target \
  --auth-mode login
```

### Step 5: Verify the target version

Inspect the target state to confirm it contains the expected resources:

```bash
# Check the number of resources
jq '.resources | length' /tmp/tfstate-backup/dev.terraform.tfstate.target

# List resource types
jq '.resources[].type' /tmp/tfstate-backup/dev.terraform.tfstate.target | sort | uniq -c
```

**Expected:** the output should list the resources you expect for the chosen point in time.

**If `jq` is not installed:** `sudo apt install jq`.

### Step 6: Restore the target version

Upload the target version to the current blob:

```bash
az storage blob upload \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --name dev.terraform.tfstate \
  --file /tmp/tfstate-backup/dev.terraform.tfstate.target \
  --auth-mode login \
  --overwrite
```

**Note:** this creates a new version of the blob with the content of the target version. The old versions remain accessible.

### Step 7: Verify with Terraform

Navigate to the Terraform environment and run a plan:

```bash
cd terraform/environments/dev
terraform init -reconfigure
terraform plan
```

**What to expect:**

- If the state matches the actual infrastructure: `No changes. Your infrastructure matches the configuration.`
- If the state does not match: `terraform plan` will show changes. This is expected if the state is from a different point in time. Review the plan carefully.

### Step 8: Confirm recovery

If the plan is consistent with the expected infrastructure, the recovery is complete.

If the plan shows unexpected changes, you may have chosen the wrong version. Return to Step 2.

### Step 9: Clean up

```bash
rm -rf /tmp/tfstate-backup
```

---

## Procedure B — Recover a Deleted Blob

**Scenario:** the state blob `dev.terraform.tfstate` was deleted.

### Step 1: List deleted blobs

```bash
az storage blob list \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --auth-mode login \
  --include d \
  --query "[?name=='dev.terraform.tfstate'].{Name:name, Deleted:deleted, DeletedTime:properties.deletedTime, RemainingRetentionDays:properties.remainingRetentionDays}" \
  -o table
```

**What to look for:**

- `Deleted: true` indicates the blob is soft-deleted.
- `DeletedTime` is when it was deleted.
- `RemainingRetentionDays` is how many days until permanent deletion.

### Step 2: Undelete the blob

```bash
az storage blob undelete \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --name dev.terraform.tfstate \
  --auth-mode login
```

### Step 3: Verify the recovery

```bash
az storage blob show \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --name dev.terraform.tfstate \
  --auth-mode login \
  --query "{Name:name, Size:properties.contentLength, LastModified:properties.lastModified}" \
  -o table
```

**Expected:** the blob appears with its original content.

### Step 4: Verify with Terraform

```bash
cd terraform/environments/dev
terraform init -reconfigure
terraform plan
```

---

## Procedure C — Recover a Deleted Container

**Scenario:** the container `tfstate` was deleted.

### Step 1: List deleted containers

```bash
az storage container list \
  --account-name tfstatejcsredatabricks \
  --auth-mode login \
  --include d \
  --query "[?name=='tfstate'].{Name:name, Deleted:deleted, DeletedTime:properties.deletedTime, RemainingRetentionDays:properties.remainingRetentionDays}" \
  -o table
```

### Step 2: Undelete the container

```bash
az storage container undelete \
  --name tfstate \
  --account-name tfstatejcsredatabricks \
  --auth-mode login
```

### Step 3: Verify the recovery

```bash
az storage container show \
  --name tfstate \
  --account-name tfstatejcsredatabricks \
  --auth-mode login \
  -o table
```

### Step 4: List the blobs in the recovered container

```bash
az storage blob list \
  --container-name tfstate \
  --account-name tfstatejcsredatabricks \
  --auth-mode login \
  --include v \
  --query "[?name=='dev.terraform.tfstate'].{Version:versionId, Modified:properties.lastModified}" \
  -o table
```

### Step 5: Verify with Terraform

```bash
cd terraform/environments/dev
terraform init -reconfigure
terraform plan
```

---

## Common Scenarios

| Scenario | Procedure | Estimated time |
|----------|-----------|----------------|
| State file corrupted after a bad apply | A | 15 minutes |
| State file deleted accidentally | B | 5 minutes |
| Container deleted accidentally | C | 10 minutes |
| Rollback to recover from a destructive change | A | 15 minutes |
| Verification of recovery procedure (test) | A | 10 minutes |

---

## Prevention

The following practices prevent most state-related incidents:

1. **Never edit the state manually.** Use `terraform state` commands if you need to modify it.
2. **Always run `terraform plan` before `apply`.** The plan shows what will change.
3. **Back up the state before risky operations.** Download the current blob before a destructive apply.
4. **Use versioning.** Enabled in Phase 9. It retains previous versions for 30 days.
5. **Use locking.** The Azure backend uses leases to prevent concurrent modification.
6. **Use `terraform state rm` instead of direct deletion.** When removing resources from the state, use the proper command.

---

## Testing

The recovery procedures are tested in Phase 9, Sub-etapa 9.2, Parte 3.
The test log is documented in `docs/operations/dr-test-log.md`.

---

## Related Documents

- [Disaster Recovery Reference](../disaster-recovery.md)
- [Phase 9 — Disaster Recovery](../../phases/phase-9-dr.md)
- [Operations README](../README.md)
- Terraform documentation: state and backend

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial runbook |