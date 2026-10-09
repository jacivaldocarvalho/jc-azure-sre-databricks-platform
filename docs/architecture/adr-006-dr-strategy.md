# ADR-006 — Disaster Recovery Strategy

**Status:** Accepted
**Date:** 2026-10-09
**Deciders:** Project author
**Context:** Phase 9 (Disaster Recovery)

---

## Context and Problem Statement

Phase 9 required the project to define a coherent disaster recovery (DR)
strategy. Several questions had to be answered before any implementation:

1. What components are covered by the DR strategy?
2. What are the RTO and RPO targets for each component?
3. What recovery strategies are used?
4. What is out of scope, and why?
5. How are the strategies validated?

This ADR captures the reasoning behind each decision.

---

## Context: Project Constraints

The disaster recovery strategy is shaped by three constraints:

### 1. Portfolio context, not production

The project is a portfolio demonstration, not a production system. The
DR strategy needs to be **appropriate for the scope**, not over-engineered.
A production system might justify multi-region failover and continuous
replication; a portfolio project does not.

### 2. Azure for Students subscription

The subscription does not allow:

- Geo-redundant storage (GRS, RA-GRS)
- Azure Site Recovery
- Continuous backup of the Databricks Workspace
- Multi-region deployments

These are documented as out of scope.

### 3. Reproducibility over availability

The project was designed for **reproducibility**: everything can be
reconstructed from code, documentation, or public data. The DR strategy
leans on this property rather than on expensive redundancy.

---

## Decision 1 — Define RTO/RPO before implementation

### Problem

A common mistake in DR planning is to start with tools (backup scripts,
replication) without knowing what the objectives are. This leads to
either over-investment or under-investment.

### Options

| Option | Description |
|--------|-------------|
| A | Choose the tools first, then define objectives |
| B | Define RTO/RPO first, then choose tools that meet them |

### Decision

**Option B.**

The document `docs/operations/disaster-recovery.md` defines:

- An inventory of all components
- A criticality classification (P0 to P3)
- RTO and RPO objectives for each component
- The recovery strategy for each component
- What is out of scope and why

### Rationale

- Every component has a defined objective. There is no ambiguity.
- The tools and scripts serve the objectives, not the other way around.
- The document is auditable: it can be reviewed and updated as the
  project evolves.

### Consequences

**Positive:**
- Clear, measurable objectives
- Justified investment in recovery capabilities
- Documented reasoning for future maintainers

**Negative:**
- Slower to start (no immediate "let's write a backup script")

---

## Decision 2 — Recovery by re-provisioning for infrastructure

### Problem

Infrastructure components (VNet, Storage Account, Databricks Workspace,
Key Vault) can be recovered by:

- Restoring from backup (if backups exist)
- Re-provisioning from code (if the code is reproducible)

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Backup the resources and restore them | Expensive; complex; not needed if the code is reproducible |
| B | Re-provision from Terraform code | Fast; zero cost; relies on the code being up to date |

### Decision

**Option B — re-provision from Terraform code.**

### Rationale

- The entire infrastructure is defined in Terraform. Recreating it is
  a matter of running `terraform apply`.
- The Terraform state is preserved in Azure Storage (with versioning
  enabled in Phase 9).
- Backing up the resources would duplicate what Terraform already
  provides.
- The re-provisioning is deterministic and auditable.

### Consequences

**Positive:**
- Zero cost for infrastructure backup
- Recovery is fast (15-25 minutes)
- The recovery uses the same code as the original deployment

**Negative:**
- Requires the Terraform state to be intact
- Requires the Terraform code to be up to date with the environment

### Mitigations

- The state backend has versioning and soft delete enabled (Sub-etapa 9.2)
- The state is preserved across `terraform destroy` cycles
- The code is in Git, which is replicated by GitHub

---

## Decision 3 — Recovery by re-processing for data

### Problem

Data components (Delta Lake raw and processed) can be recovered by:

- Restoring from backup
- Re-fetching from the source (BCB API) and re-processing

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Backup the Delta Lake to another storage account | Expensive; complex |
| B | Re-fetch and re-process from the BCB API | Free; deterministic; requires the pipeline to work |

### Decision

**Option B — re-fetch and re-process.**

### Rationale

- The source (BCB API) is public and free.
- The pipeline is deterministic: the same input produces the same output.
- Re-processing takes only a few minutes (the pipeline runs in ~25 seconds).
- The data is already reproducible by design; backing it up would be redundant.

### Consequences

**Positive:**
- Zero cost for data backup
- Data is always fresh
- The recovery validates the pipeline itself

**Negative:**
- If the BCB API changes or becomes unavailable, the data cannot be re-fetched
- Historical data from previous months could be lost if the pipeline only fetches a limited window

### Mitigations

- The BCB API is authoritative and stable
- If needed, a snapshot of the data can be committed to Git (not done in this project)

---

## Decision 4 — Versioning and soft delete for the Terraform state

### Problem

The Terraform state is the only component that is **not reproducible**
from source code alone. Its loss would be catastrophic: the project
would lose the ability to manage the infrastructure without manual
reconstruction.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Rely on the Azure Storage LRS (3 copies in one datacenter) | Free; protects against disk failure, not user error |
| B | Enable blob versioning + soft delete | Cheap; protects against user error and corruption |
| C | Migrate to GRS (geo-redundant) | Expensive; protects against regional outage |

### Decision

**Option B — enable blob versioning and soft delete.**

### Rationale

- Versioning retains previous versions of the state for 30 days. Any
  corruption can be rolled back.
- Soft delete retains deleted blobs for 30 days. Any accidental
  deletion can be recovered.
- The cost is negligible (~$0.01/month).
- GRS would add cost without a corresponding benefit for a portfolio
  project in a single region.

### Consequences

**Positive:**
- Protects against corruption and accidental deletion
- Zero cost in practice
- Enables the rollback procedure documented in the runbooks

**Negative:**
- The state history is retained for 30 days. After that, versions are
  permanently deleted.
- The versioning applies to all blobs in the storage account, not just
  the state file.

### Mitigations

- The retention of 30 days is more than sufficient for this project.
- The state file is small (183 bytes empty, up to 80 KB when populated).

---

## Decision 5 — Documented runbooks for common scenarios

### Problem

DR is invoked under pressure. Without documented procedures, the
recovery is ad-hoc and error-prone.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | No runbooks, rely on tribal knowledge | Fast to start; fragile |
| B | Runbooks in Markdown with commands | Requires up-front investment; robust |
| C | Automated scripts only | Fast execution; no context for decisions |

### Decision

**Option B — runbooks in Markdown, complemented by scripts where useful.**

### Rationale

- Runbooks provide context: why each step is done, what to expect, how
  to handle deviations.
- Scripts are used for repeated operations (backup, restore), but the
  runbook explains when and why to run them.
- Markdown runbooks live in Git and are versioned along with the code.

### Consequences

**Positive:**
- Recovery is predictable
- New operators can execute the procedures
- Runbooks can be tested (see Decision 6)

**Negative:**
- Runbooks require maintenance when the infrastructure changes

### Mitigations

- Runbooks are reviewed at the start of each phase
- The `dr-test-log.md` documents deviations and lessons learned

---

## Decision 6 — Validate runbooks with tabletop exercises

### Problem

A runbook that has never been tested is a hope, not a plan.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | No tests | Fast; the plan is theoretical |
| B | Tabletop exercises on safe scenarios | Requires time; validates the plan |
| C | Full drills (destroy and recreate) | Most realistic; expensive and risky |

### Decision

**Option B — tabletop exercises on safe scenarios.**

### Rationale

- The exercises validate the procedures without risking the environment.
- The chosen scenarios (state rollback, secret recovery) are safe and
  fast to execute.
- The exercises are documented in `dr-test-log.md`.
- Full drills are reserved for scenarios where the value justifies the
  cost (e.g., a complete re-provisioning drill in Phase 10).

### Consequences

**Positive:**
- The procedures are validated
- Deviations and lessons learned are documented
- The RTO targets are validated (or adjusted) based on real measurements

**Negative:**
- The tests do not exercise the full end-to-end recovery for all
  scenarios

### Mitigations

- The most critical scenarios (state, secrets) are tested
- The remaining scenarios are documented with estimates
- A full drill is planned for Phase 10

---

## Out of Scope

The following scenarios are documented as **out of scope** for this
project, with the reasoning.

| Scenario | Reason |
|----------|--------|
| Multi-region failover | Requires a paid subscription and geo-redundant resources |
| Continuous replication of the Data Lake | Requires GRS or RA-GRS, not available on the current subscription |
| Automated backup of the Databricks Workspace | Requires a running cluster and a paid backup solution |
| Azure Site Recovery | Requires VMs, which are not used in this project |
| Backup of historical Application Insights metrics | Loss is acceptable; the pipeline continues emitting new metrics |
| Backup of the Kind cluster | The cluster is ephemeral; it is reproduced from code |

The list is documented in `docs/operations/disaster-recovery.md`.

---

## Consequences

### Positive

- **Clear objectives.** Every component has an RTO and RPO.
- **Appropriate cost.** No expensive redundancy for a portfolio project.
- **Reproducibility-based.** The strategy leans on the project's
  reproducibility rather than on backups.
- **Validated.** Two scenarios have been tested and documented.
- **Documented.** Three runbooks and one test log are in the repository.

### Negative

- **Limited scope.** Multi-region and continuous replication are not
  covered.
- **No automated re-provisioning.** The recovery is manual (with
  documented procedures).
- **Historical metrics can be lost.** Acceptable for the project.

---

## Alternatives Considered Overall

### Backup every component

Considered. Rejected because most components are reproducible from code
or public data. Backing them up would be redundant and expensive.

### Use Azure Backup for everything

Considered. Rejected because Azure Backup is designed for VMs, SQL
databases, and file shares, not for the types of resources used in this
project (VNet, Storage Account, Databricks Workspace).

### Adopt a full DR tool (Azure Site Recovery)

Rejected because it requires VMs, which are not used in this project.

### Use a multi-region active-active setup

Rejected because the subscription does not allow it, and the cost would
be prohibitive for a portfolio.

---

## References

- [Disaster Recovery Reference](../operations/disaster-recovery.md)
- [DR Test Log](../operations/dr-test-log.md)
- [Phase 9 — Disaster Recovery](../phases/phase-9-dr.md)
- [ADR-001 — Databricks Cluster Limitation](adr-001-databricks-cluster-limitation.md)
- [ADR-005 — AKS Local-First Strategy](adr-005-aks-local-first.md)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial decision recorded |