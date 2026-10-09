# Disaster Recovery

Reference document for the disaster recovery posture of the
JC-Azure SRE Databricks Platform.

---

## Purpose

This document defines:

- The components covered by the disaster recovery strategy
- The criticality classification of each component
- The Recovery Time Objective (RTO) and Recovery Point Objective (RPO)
  for each component
- The recovery strategy for each component
- The testing procedure for the recovery plans

The document is a living reference. It is reviewed whenever a new
component is added or an existing component changes.

---

## Scope

This document covers the **development environment** (`dev`) of the
project. Production environments would require a different DR posture,
typically with higher costs and tighter RTO/RPO.

---

## Concepts

### RTO — Recovery Time Objective

The maximum acceptable time between the failure of a component and the
restoration of its service. Measured in hours or days.

### RPO — Recovery Point Objective

The maximum acceptable data loss, measured in time. If the RPO is 24
hours, losing up to 24 hours of data is acceptable; losing more is not.

### Criticality Classification

| Level | Meaning | Business Impact |
|-------|---------|-----------------|
| **P0 — Critical** | Loss causes immediate, unrecoverable impact | The project cannot function without it |
| **P1 — High** | Loss causes significant delay or rework | The project can function, but with substantial manual effort |
| **P2 — Medium** | Loss is recoverable with modest effort | The project continues, but with temporary inconvenience |
| **P3 — Low** | Loss is inconsequential | No business impact |

---

## Component Inventory

### Configuration and State

| Component | Location | Criticality |
|-----------|----------|-------------|
| Terraform state | Azure Storage `tfstatejcsredatabricks` | **P0** |
| Source code | GitHub repository | **P0** |
| Secrets (Application Insights connection string) | Azure Key Vault `dev-sredatabricks-kv` | **P1** |
| Service Principal (Azure DevOps) | Microsoft Entra ID | **P1** |

### Data

| Component | Location | Criticality |
|-----------|----------|-------------|
| Raw data (BCB series) | Delta Lake `raw/` + BCB API | **P3** |
| Processed data (aggregations, variations) | Delta Lake `processed/` | **P3** |
| Executive summaries | Delta Lake `processed/summaries/` | **P3** |

### Infrastructure (provisioned via Terraform)

| Component | Location | Criticality |
|-----------|----------|-------------|
| Resource Group, VNet, subnets, NSG | Azure | **P2** |
| Storage Account (ADLS Gen2) | Azure | **P1** |
| Databricks Workspace | Azure | **P2** |
| Key Vault | Azure | **P1** |
| Application Insights, Log Analytics | Azure | **P3** |
| AKS module (not applied) | Terraform code | **P3** |
| Azure OpenAI module (not applied) | Terraform code | **P3** |

### Local Development

| Component | Location | Criticality |
|-----------|----------|-------------|
| Local `spark-warehouse/` | Developer machine | **P3** |
| Kind cluster configuration | Git + local Docker | **P3** |
| `.env` file | Developer machine | **P2** |

---

## Criticality Justification

### P0 — Critical

**Terraform state**
The state is the only source of truth about what resources exist and how
they are configured. Losing it means losing the ability to manage the
infrastructure without manual reconstruction. It cannot be regenerated
from source code alone.

**Source code**
The entire project is defined in the repository. Losing it means losing
months of work. The GitHub repository is the primary store, but it relies
on GitHub's availability.

### P1 — High

**Secrets**
The Application Insights connection string is required for the pipeline
to send metrics. Losing it means the observability pipeline stops
working. It can be recreated, but requires coordination between the
pipeline and the Application Insights instance.

**Service Principal**
The Azure DevOps Service Principal authenticates the CI/CD pipelines.
Losing it means the pipelines cannot run. It can be recreated, but
requires reconfiguring the Federated Credential and role assignments.

**Storage Account (ADLS Gen2)**
Contains the Delta Lake data. The data is reproducible, but the storage
account itself holds the configuration for containers, HNS, and access
controls.

### P2 — Medium

**Resource Group, VNet, subnets, NSG**
Fully reproducible via Terraform. The only impact is the time to
re-provision.

**Databricks Workspace**
Reproducible via Terraform. Re-provisioning takes ~15 minutes.

**`.env` file**
Contains configuration values. Can be reconstructed from the
`.env.example` and the documentation.

### P3 — Low

**Raw and processed data**
Entirely reproducible from the BCB API in a few minutes. The processed
data is derived from raw data via a deterministic pipeline.

**Application Insights, Log Analytics**
Historical metrics and logs. Loss is acceptable. New metrics will be
collected from the moment the service is restored.

**AKS and OpenAI modules**
Not applied. Exist only as code in the repository.

**Local `spark-warehouse/`**
Reproducible via `make pipeline-run`.

**Kind cluster**
Reproducible via `make kind-up`.

---

## RTO and RPO by Component

The table below defines the objectives. The actual recovery time is
measured during the tabletop exercises (Sub-etapa 9.4).

### P0 — Critical Components

| Component | RTO | RPO | Rationale |
|-----------|-----|-----|-----------|
| Terraform state | 4 hours | 24 hours | State changes are infrequent; losing 24h of state changes means at most one apply is lost |
| Source code | 1 hour | 0 (Git push) | Code is pushed frequently; recovery is a `git clone` |

### P1 — High Components

| Component | RTO | RPO | Rationale |
|-----------|-----|-----|-----------|
| Application Insights secret | 2 hours | 7 days | Soft delete retention is 7 days; recreation is straightforward |
| Service Principal | 4 hours | N/A | Recreation requires re-doing the Federated Credential setup |
| Storage Account | 4 hours | 24 hours | Data loss is bounded by the pipeline's re-run; storage config is reproducible |

### P2 — Medium Components

| Component | RTO | RPO | Rationale |
|-----------|-----|-----|-----------|
| Resource Group, VNet, NSG | 2 hours | 0 | Terraform apply is deterministic |
| Databricks Workspace | 4 hours | N/A | Workspace is stateless; re-provisioning takes ~15 minutes |
| `.env` file | 30 minutes | 24 hours | Reconstructible from documentation |

### P3 — Low Components

| Component | RTO | RPO | Rationale |
|-----------|-----|-----|-----------|
| Raw and processed data | 1 hour | 30 days | Reproducible from the BCB API |
| Application Insights metrics | 8 hours | 30 days | Loss is acceptable; new metrics will flow |
| AKS, OpenAI modules | N/A | N/A | Not applied |
| Local `spark-warehouse/` | 1 hour | N/A | Reproducible via `make pipeline-run` |
| Kind cluster | 1 hour | N/A | Reproducible via `make kind-up` |

---

## Recovery Strategies

### Strategy 1: Re-Provisioning (for infrastructure)

**Applicable to:** VNet, subnets, NSG, Storage Account, Databricks Workspace, Key Vault, Application Insights, Log Analytics.

**Approach:** run `terraform apply` against the preserved Terraform state. Terraform detects missing resources and recreates them.

**Prerequisite:** the Terraform state must be intact.

### Strategy 2: Re-Processing (for data)

**Applicable to:** Delta Lake raw and processed data.

**Approach:** run `make pipeline-run`. This re-fetches the data from the BCB API and re-processes it.

**Prerequisite:** the pipeline code and Python environment must be intact.

### Strategy 3: Restoration from Backup (for the Terraform state)

**Applicable to:** the Terraform state file.

**Approach:** restore the state from a previous version in Azure Storage. The state backend is configured with versioning, allowing rollback to any previous version within the retention window.

**Prerequisite:** versioning must be enabled on the storage account (Sub-etapa 9.2).

### Strategy 4: Recreation from Documentation (for the Service Principal)

**Applicable to:** the Azure DevOps Service Principal and its Federated Credential.

**Approach:** recreate the App Registration, the Federated Credential, the role assignment, and the Service Connection in Azure DevOps, following the documented procedure.

**Prerequisite:** the documentation in `docs/phases/phase-4-cicd.md`.

### Strategy 5: Soft Delete Recovery (for Key Vault secrets)

**Applicable to:** secrets in the Key Vault.

**Approach:** recover the secret from soft delete. Retention is 7 days.

**Prerequisite:** the Key Vault must be intact (soft delete is per-vault).

### Strategy 6: Git Clone (for source code)

**Applicable to:** the entire project's source code.

**Approach:** clone the repository from GitHub.

**Prerequisite:** GitHub availability and access to the repository.

---

## Scenario Coverage

The following table maps common failure scenarios to their recovery strategies.

| Scenario | Components Affected | Strategy |
|----------|---------------------|----------|
| Accidental deletion of a secret in Key Vault | Application Insights connection string | Soft delete recovery |
| Corruption of the Terraform state | Terraform state | Restoration from backup |
| Loss of a developer machine | Local files, environment | Git clone + re-provisioning |
| Accidental deletion of a Storage Account container | Delta Lake data | Re-processing |
| Loss of the Azure DevOps Service Principal | CI/CD pipelines | Recreation from documentation |
| Regional outage of Azure | All Azure resources | Regional failover (documented as out-of-scope for the dev environment) |
| Compromise of a secret | Multiple | Rotation + recreation |

---

## Out of Scope

The following scenarios are documented as **out of scope** for this project, with the reasoning.

| Scenario | Reason |
|----------|--------|
| Multi-region failover | Requires a paid subscription and geo-redundant resources |
| Continuous replication of the Data Lake | Requires GRS or RA-GRS storage, not provisionable on the current subscription |
| Automated backup of the Databricks Workspace | Requires a running cluster and a paid backup solution |
| Azure Site Recovery | Requires VMs, which are not used in this project |
| Backup of historical Application Insights metrics | Loss of historical metrics is acceptable; the pipeline continues emitting new ones |
| Backup of the Kind cluster | The cluster is ephemeral by design; it is reproduced from code |

---

## Testing

The disaster recovery plans are validated through tabletop exercises,
documented in [Sub-etapa 9.4](../phases/phase-9-dr.md). Each exercise:

1. Describes a failure scenario
2. Lists the expected steps to recover
3. Executes the steps (when possible)
4. Measures the actual RTO
5. Compares it to the objective
6. Documents deviations

The exercises are designed to be safe: they never destroy production data
or incur unbounded costs.

---

## Roles and Responsibilities

This is a solo portfolio project. All roles are performed by the project
author.

| Role | Responsibility |
|------|---------------|
| Operator | Executes the recovery steps in case of failure |
| Reviewer | Validates the recovery plan and the test results |
| Owner | Makes decisions about RTO/RPO and prioritizes fixes |

---

## Review Cycle

This document is reviewed:

- Whenever a new component is added
- After each tabletop exercise
- At the start of each new phase
- Annually, even if no changes occurred

---

## Related Documents

- [Phase 9 — Disaster Recovery](../phases/phase-9-dr.md)
- [ADR-006 — DR Strategy](../architecture/adr-006-dr-strategy.md) (to be created)
- [Operations README](README.md)
- [Security Model](../architecture/security-model.md)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial document with RTO/RPO definitions and inventory |
