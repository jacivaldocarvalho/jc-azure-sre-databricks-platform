# Phase 9 — Disaster Recovery

**Status:** Completed
**Duration:** Multi-iteration (RTO/RPO definition, backend hardening, runbooks, tabletop exercises)
**Dependencies:** Phase 8 (AKS and Containerized Workloads)

---

## Objective

Define and validate a disaster recovery strategy for the project. The
phase covers:

- An inventory of components with criticality classification
- RTO and RPO objectives for each component
- Recovery strategies for the covered scenarios
- Documented runbooks that any operator can follow
- Tabletop exercises to validate the runbooks
- Transparent documentation of what is out of scope

The goal is not to build an enterprise-grade DR solution, but to
demonstrate that a small project can have a coherent, tested, and
documented recovery posture.

---

## Context

### Why DR for a portfolio project

Two reasons:

1. **SRE discipline.** SRE is about reliability. Reliability includes
   what happens when things fail. A project that claims to be SRE
   without a DR plan is incomplete.

2. **Realistic constraints.** The project runs on a constrained
   subscription. The DR strategy must be appropriate to that reality,
   not aspirational.

### Constraints

| Constraint | Impact |
|------------|--------|
| Azure for Students | No GRS, no ASR, no multi-region |
| Portfolio scope | No enterprise-grade tools |
| Single developer | No on-call, no 24/7 monitoring |
| Reproducibility by design | Backups are mostly unnecessary |

### Principles applied

1. **Define objectives before tools.** RTO and RPO come first; the
   tools follow.
2. **Prefer reproducibility over redundancy.** Everything that can be
   regenerated from code is not backed up.
3. **Protect what cannot be regenerated.** The Terraform state is the
   only irreplaceable artifact.
4. **Document and test.** A runbook that was not executed is a hope.
5. **Be honest about scope.** What is not covered is documented as out
   of scope with the reasoning.

---

## Implementation

### 1. Disaster Recovery Reference Document

Created `docs/operations/disaster-recovery.md` with:

- Component inventory
- Criticality classification (P0 to P3)
- RTO and RPO for each component
- Six recovery strategies
- Scenario coverage table
- Out-of-scope list with reasoning

The document is the reference for the entire DR posture.

### 2. Terraform state backend hardening

Enabled on the state storage account `tfstatejcsredatabricks`:

| Feature | Setting |
|---------|---------|
| Blob versioning | Enabled |
| Blob soft delete | 30 days |
| Container soft delete | 30 days |

The setup is automated by `scripts/protect-tfstate-backend.sh`, which
is idempotent and can be run repeatedly.

**A note on retroactive versioning:** when versioning was enabled, Azure
reconstructed versions from the internal operation journal. The state
now has over 300 versions spanning from 2026-08-17 to today. This is a
bonus for DR: the state history is complete.

### 3. Runbooks

Created four runbooks under `docs/operations/runbooks/`:

| Runbook | Purpose |
|---------|---------|
| `recover-terraform-state.md` | Rollback, undelete blob, undelete container |
| `recover-keyvault-secret.md` | Undelete, re-provision, or recreate a Key Vault secret |
| `reprovision-environment.md` | Full rebuild of the Azure environment |
| `recover-from-lost-machine.md` | Recover the dev environment after machine loss |

Each runbook follows a consistent structure:

- When to use
- Prerequisites
- Recovery decision tree (ASCII diagram)
- Step-by-step procedures
- Common scenarios with time estimates
- Prevention
- Testing reference

### 4. Test log

Created `docs/operations/dr-test-log.md` to record every executed test.

**Tests executed:**

| # | Scenario | Status | Duration |
|---|----------|--------|----------|
| 1 | Rollback of the Terraform state | Passed | ~15 minutes |
| 2 | Recovery of a Key Vault secret | Passed | ~3 minutes (post-apply) |
| 5 | Recovery from a lost machine | Partial | Not measured |

### 5. ADR-006

Documented the strategic decisions in
`docs/architecture/adr-006-dr-strategy.md`:

1. Define RTO/RPO before choosing tools
2. Re-provision infrastructure from code
3. Re-process data from the source
4. Enable versioning and soft delete for the state
5. Document runbooks for common scenarios
6. Validate runbooks with tabletop exercises

---

## Architecture

### Recovery flow

```
              ┌─────────────────────────────────────┐
              │  Failure detected                   │
              └──────────────────┬──────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ State      │    │ Secrets    │    │ Machine    │
       │ problem    │    │ problem    │    │ lost       │
       └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
             │                 │                 │
             ▼                 ▼                 ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ Runbook:   │    │ Runbook:   │    │ Runbook:   │
       │ recover-   │    │ recover-   │    │ recover-   │
       │ terraform- │    │ keyvault-  │    │ from-lost- │
       │ state.md   │    │ secret.md  │    │ machine.md │
       └────────────┘    └────────────┘    └────────────┘
```

### Component criticality

| Level | Components | RTO |
|-------|-----------|-----|
| P0 | Terraform state, source code | 1-4 hours |
| P1 | Secrets, Service Principal, Storage Account | 2-4 hours |
| P2 | Resource Group, VNet, Databricks Workspace, `.env` | 30 min - 4 hours |
| P3 | Data, metrics, Kind cluster, local warehouse | 1-8 hours |

---

## Validation

### Test 1 — Rollback of the Terraform state

Executed: listed versions, backed up the current state, downloaded a
previous version, restored it, verified with `terraform plan`, restored
the backup.

**Result:** Passed. ~15 minutes. Within the RTO target of 4 hours.

### Test 2 — Recovery of a Key Vault secret

Executed: after a `terraform apply` recreated the environment, the
Key Vault was empty. Retrieved the connection string, uploaded it to
the Key Vault, verified via Azure CLI and Python.

**Result:** Passed. ~3 minutes (after apply). Within the RTO target of
2 hours.

### Test 5 — Recovery from a lost machine

Partially validated by inspecting each component (repository, `.env`,
state, secrets, pipeline). Full drill not executed.

**Result:** Partial. Individual components validated; end-to-end
recovery documented but not executed.

### Local checks

| Check | Result |
|-------|--------|
| `make protect-tfstate` | Backend protected |
| `make tfstate-versions` | 300+ versions listed |
| Runbooks executable | Tested for scenarios 1 and 2 |

---

## Lessons Learned

### What worked well

- **Defining objectives first.** The RTO/RPO exercise clarified what
  mattered and what did not. Without it, the DR strategy would have
  been guesswork.
- **Reproducibility as a DR property.** The project was already
  reproducible by design. The DR strategy simply formalized this.
- **Retroactive versioning.** When versioning was enabled, Azure
  provided a complete state history from the beginning of the project.
  This is a significant unplanned benefit.
- **Runbooks as code.** Living in Git alongside the code means they
  are versioned, reviewed, and updated with the project.

### Adjustments made

1. **Backend protection first.** Before writing runbooks, we hardened
   the state backend. This ensured the recovery procedure would have
   something to recover from.

2. **Test before documenting.** The `dr-test-log.md` was written as
   tests were executed, not before. This kept the log honest.

3. **Accept partial validation.** The lost machine test was not
   executed end-to-end. Documenting it as partial is more honest than
   claiming it passed.

### What would be done differently

- **Automate the Key Vault secret population.** Currently it is a
  manual step after every `terraform apply`. A script or a Terraform
  null_resource could do it.
- **Test the full re-provisioning drill.** This would take 30-50
  minutes and consume credit. It is planned for Phase 10.
- **Consider Terraform-managed secrets.** Some teams manage secrets
  with Terraform's `azurerm_key_vault_secret`. This project chose not
  to, to avoid storing secrets in the state. Worth revisiting.

---

## Artifacts

### Documentation

| Artifact | Path | Purpose |
|----------|------|---------|
| DR Reference | `docs/operations/disaster-recovery.md` | RTO/RPO definitions and inventory |
| DR Test Log | `docs/operations/dr-test-log.md` | Record of executed tests |
| ADR-006 | `docs/architecture/adr-006-dr-strategy.md` | Strategic decisions |
| Runbook — State | `docs/operations/runbooks/recover-terraform-state.md` | Rollback and undelete procedures |
| Runbook — Secret | `docs/operations/runbooks/recover-keyvault-secret.md` | Secret recovery procedures |
| Runbook — Re-provision | `docs/operations/runbooks/reprovision-environment.md` | Full rebuild procedure |
| Runbook — Lost Machine | `docs/operations/runbooks/recover-from-lost-machine.md` | Machine recovery procedure |

### Code

| Artifact | Path | Purpose |
|----------|------|---------|
| Backend protection script | `scripts/protect-tfstate-backend.sh` | Enable versioning and soft delete |
| Makefile targets | `Makefile` | `protect-tfstate`, `tfstate-versions` |

### Azure configuration

| Setting | Value |
|---------|-------|
| Blob versioning | Enabled on `tfstatejcsredatabricks` |
| Blob soft delete | 30 days |
| Container soft delete | 30 days |

---

## Out of Scope

The following capabilities are documented as out of scope for the
current subscription. Each is a candidate for a future phase if the
project migrates to a paid subscription.

| Capability | Reason | Estimated effort |
|-----------|--------|------------------|
| Multi-region failover | Requires paid subscription and geo-redundant resources | High |
| GRS / RA-GRS storage | Same | Low |
| Automated backup of the Databricks Workspace | Requires a running cluster and a paid backup solution | Medium |
| Azure Site Recovery | Requires VMs (not used in this project) | N/A |
| Backup of historical Application Insights metrics | Loss is acceptable | N/A |

---

## Next Phase

[Phase 10 — Cost Optimization and Governance](../phases/phase-10-governance.md):
review costs, adopt FinOps practices, and formalize governance.