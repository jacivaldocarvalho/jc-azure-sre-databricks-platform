# Disaster Recovery Test Log

Record of disaster recovery tests executed on the project.

---

## Purpose

This log documents every disaster recovery test executed on the project.
Each entry records:

- The date and time of the test
- The scenario being tested
- The procedure followed (from the runbook)
- The time taken to execute the procedure
- The result (success, partial, failure)
- Deviations or lessons learned

The log is a reference for future audits and for validating the RTO/RPO
objectives defined in `docs/operations/disaster-recovery.md`.

---

## Test Index

| # | Date | Scenario | Status | Duration | RTO Target |
|---|------|----------|--------|----------|-----------|
| 1 | 2026-10-09 | Rollback of the Terraform state to a previous version | Passed | ~15 minutes | 4 hours |
| 2 | 2026-10-09 | Recovery of a Key Vault secret after environment recreation | Passed | ~3 minutes (post-apply) | 2 hours |
| 3 | (pending) | Recovery of a deleted Key Vault secret (soft delete) | — | — | 2 hours |
| 4 | (pending) | Recovery of a deleted Terraform state blob | — | — | 4 hours |
| 5 | 2026-10-09 | Recovery from a lost developer machine | Partial | Not measured | 8 hours |

---

## Test 1 — Rollback of the Terraform State to a Previous Version

**Date:** 2026-10-09
**Scenario:** The Terraform state needs to be rolled back to a previous
version. This simulates recovery from a corrupted state or from a
destructive change.

**Runbook:** [recover-terraform-state.md](runbooks/recover-terraform-state.md), Procedure A

### Procedure Executed

1. Listed available versions with `make tfstate-versions`
2. Backed up the current state to a local file
3. Downloaded a specific version using `--version-id`
4. Inspected the downloaded version (validated JSON)
5. Uploaded the version to the current blob with `--overwrite`
6. Verified with `terraform init -reconfigure` and `terraform plan`
7. Restored the backup
8. Verified the restoration
9. Cleaned up the temporary directory

### Observations

| Step | Observation |
|------|-------------|
| 1 | The list returned 300+ versions spanning from 2026-08-17 to 2026-10-09 |
| 2 | The current state file is 183 bytes (environment destroyed) |
| 3 | The chosen version was also 183 bytes (from 2026-10-01) |
| 4 | JSON validation passed |
| 5 | Upload completed successfully |
| 6 | `terraform plan` showed `Plan: 29 to add, 0 to change, 0 to destroy` — consistent with the destroyed environment |
| 7 | Upload of the backup completed successfully, creating a new version |
| 8 | `terraform plan` showed the same result as step 6 |
| 9 | Clean up completed |

### Timing

| Phase | Duration |
|-------|----------|
| Preparation (list + backup) | ~2 minutes |
| Download + inspect | ~2 minutes |
| Restore + verify | ~5 minutes |
| Restore backup + verify | ~5 minutes |
| Clean up | ~1 minute |
| **Total** | **~15 minutes** |

### Result

**Passed.** The procedure works as documented.

### Deviations from the Runbook

None. The runbook was followed as written.

### Lessons Learned

1. **Versioning was retroactively populated.** When versioning was enabled,
   Azure reconstructed versions from the internal journal, providing a
   complete history back to 2026-08-17. This is a bonus for disaster
   recovery — the state history is complete.

2. **The state size is a useful signal.** Empty state = ~183 bytes.
   Populated state = tens of kilobytes. This can be used as a quick
   sanity check when choosing a version.

3. **The test is safe and reversible.** Because we always back up the
   current state before modifying, the procedure carries no risk.

### Impact on RTO

The measured time (15 minutes) is well within the RTO target of 4 hours.
The RTO could even be tightened to 1 hour for this scenario, if needed.

---

## Test 2 — Recovery of a Key Vault Secret After Environment Recreation

**Date:** 2026-10-09
**Scenario:** The Azure environment was destroyed and re-provisioned via
`terraform apply`. The Key Vault was recreated empty, and the
`applicationinsights-connection-string` secret was missing. The pipeline
could not send metrics until the secret was restored.

**Runbook:** [recover-keyvault-secret.md](runbooks/recover-keyvault-secret.md), Procedure B

### Procedure Executed

1. Ran `terraform apply` to recreate the environment (12 minutes)
2. Discovered that the Key Vault was empty (`SecretNotFound`)
3. Retrieved the new connection string from the Terraform output
4. Cleaned the file (removed the trailing newline, resulting in 248 bytes)
5. Uploaded the secret to the Key Vault via `az keyvault secret set --file`
6. Verified via Azure CLI: the secret appeared with `Enabled: true`
7. Verified via Python: `SecretClient.get_secret()` returned the value in 1.6 seconds

### Observations

| Step | Observation |
|------|-------------|
| 1 | `terraform apply` recreated 29 resources in ~12 minutes |
| 2 | `az keyvault secret show` returned `SecretNotFound` |
| 3 | `terraform output -raw` produced a new connection string (new `InstrumentationKey`) |
| 5 | `az keyvault secret set --file` succeeded; the secret ID was created with a new version |
| 6 | `Enabled: true`, `Created: 2026-10-09T22:12:05+00:00` |
| 7 | Python `SecretClient` read the secret in 1.6 seconds (token cached after first call) |

### Timing

| Phase | Duration |
|-------|----------|
| Terraform apply (before the test) | ~12 minutes |
| Retrieve connection string (step 3) | < 1 minute |
| Upload to Key Vault (step 5) | < 1 minute |
| Verification (steps 6-7) | ~2 minutes |
| **Total recovery (after apply)** | **~3 minutes** |

### Result

**Passed.** The procedure works as documented.

### Deviations from the Runbook

None. The runbook Procedure B was followed exactly. The first Python
call required a token refresh and was interrupted manually by the
operator; the second call completed in 1.6 seconds.

### Lessons Learned

1. **The secret is not managed by Terraform.** It must be re-populated
   after every `terraform destroy` + `apply` cycle. This is documented
   in the Post-Apply Checklist.
2. **The recovery is fast.** Retrieving and uploading the secret takes
   less than 3 minutes.
3. **The first `AzureCliCredential` call may be slow.** If the token
   needs to be refreshed, the call may take 10-30 seconds. Do not
   interrupt it.
4. **`az keyvault secret set --file` handles the whole value.** Using
   `--file` (rather than `--value`) avoids truncation caused by copying
   the connection string from the terminal.

### Impact on RTO

The measured time (~3 minutes) is well within the RTO target of 2 hours.

### Action Items

- [x] Populate the secret after every `terraform apply`
- [ ] Consider automating the secret population as a post-apply script (Phase 10)
- [ ] Reinforce the Post-Apply Checklist with a step to verify the secret

---

## Test 5 — Recovery from a Lost Developer Machine (Partial)

**Date:** 2026-10-09
**Scenario:** The developer's machine was lost. The recovery was
partially validated by verifying that the repository is fully
reproducible from Git and that the tooling is documented.

**Runbook:** [recover-from-lost-machine.md](runbooks/recover-from-lost-machine.md)

### Procedure Executed

The full recovery was not simulated on a clean machine. Instead, the
following aspects were validated:

1. The repository is public on GitHub and can be cloned by any user
2. The `.env.example` contains the required variables
3. The Terraform state is stored in Azure Storage, not locally
4. The secrets are stored in the Key Vault, not locally
5. The pipeline is reproducible from the source code

### Observations

| Aspect | Status |
|--------|--------|
| Repository cloneable from GitHub | Validated |
| `.env.example` completeness | Validated (contains all needed variables) |
| Terraform state in the cloud | Validated |
| Secrets in the Key Vault | Validated |
| Pipeline reproducible from code | Validated |

### Timing

Not measured. The full recovery is estimated at 45 minutes to 2 hours,
depending on whether the environment needs to be re-provisioned.

### Result

**Partial.** The individual components are validated, but the end-to-end
recovery on a clean machine was not executed.

### Deviations from the Runbook

The full procedure was not executed. The validation was done by
inspecting each component.

### Lessons Learned

- The architecture is designed for reproducibility: nothing critical
  is stored only on the local machine.
- The most time-consuming step in a real recovery would be the tool
  installation (30-60 minutes).
- A real test would require a spare machine or a VM. This can be
  scheduled for Phase 10 or as a future improvement.

### Impact on RTO

Not measured. The estimated time is well within the RTO target of 8 hours.

---

## Test 3 — Recovery of a Deleted Terraform State Blob

**Date:** (pending)
**Scenario:** The Terraform state blob was accidentally deleted.

**Runbook:** [recover-terraform-state.md](runbooks/recover-terraform-state.md), Procedure B

---

## Test 4 — Full Re-Provisioning of the Environment

**Date:** (pending)
**Scenario:** The entire Azure environment was destroyed and needs to be
re-provisioned.

**Runbook:** (to be created in Sub-etapa 9.3)

---

## Test 5 — Recovery from a Lost Developer Machine

**Date:** (pending)
**Scenario:** The developer's machine was lost. All local files need to
be recovered from Git.

**Runbook:** (to be created in Sub-etapa 9.3)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Test 1 (state rollback) executed and documented |
| 2026-10-09 | Test 2 (Key Vault secret recovery) executed and documented |
| 2026-10-09 | Test 5 (lost machine) partially validated |
