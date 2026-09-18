# ADR-001 — Databricks Cluster Limitation in Azure for Students

**Status:** Accepted
**Date:** 2026-09-18
**Deciders:** author
**Context:** Phase 3 (Data Pipeline)

---

## Context and Problem Statement

The original Phase 3 plan was to provision a Databricks cluster via Terraform, deploy notebooks to it, and execute the data pipeline directly on the cluster.

During implementation, the cluster could not be created. The failure is structural and not correctable through configuration changes in the Terraform code. This ADR documents the investigation, the alternatives considered, and the decision taken.

---

## Background

### The Subscription

The project runs on an **Azure for Students** subscription. This subscription type has properties that differ significantly from a pay-as-you-go or enterprise subscription:

- A fixed credit allocation (typically $100 USD total)
- A hard region restriction via the policy `sys.regionrestriction`
- A reduced quota for vCPUs per region
- A restricted SKU catalog

These are intentional design constraints of the subscription type, not bugs.

### The Policy: `sys.regionrestriction`

The subscription-level policy limits resource deployment to five regions:

```
eastus
northcentralus
centralus
brazilsouth
spaincentral
```

Any resource deployment outside these regions is rejected at the ARM level.

### The Quota

For each permitted region, the total regional vCPU quota for this subscription is approximately **6 vCPUs**. This quota is fixed and **cannot be increased** for Azure for Students subscriptions.

### The Databricks Requirement

A Databricks cluster requires:

- A minimum of 4 vCPUs for the driver (for any SKU in the supported list)
- Additional vCPUs for workers in multi-node clusters

For a single-node cluster, 4 vCPUs are sufficient in theory. In practice, the combination of quota, SKU availability, and Databricks' supported SKU list proved impossible to satisfy.

---

## Investigation

### Attempt 1 — `Standard_DS3_v2` in `eastus`

Failed with `SkuNotAvailable`. The `az vm list-skus` command confirmed that `Standard_DS3_v2` is not offered to this subscription in `eastus`, even though it appears in the Databricks supported SKU list.

### Attempt 2 — Other SKUs in `eastus`

Tried `Standard_DS2_v2`, `Standard_D4s_v3`, `Standard_D4as_v4`, and others. All failed with `SkuNotAvailable`. Additional SKUs from the v6 and v7 generations appear in the `az vm list-skus` output but are rejected by Databricks because they are not in the supported SKU list.

### Attempt 3 — Region Change to `brazilsouth`

Since `brazilsouth` is in the allowed regions list and is the region closest to the project owner, migrated the entire Terraform stack to `brazilsouth`.

Result: **all supported Databricks SKUs are absent**. `az vm list-skus` in `brazilsouth` returns only v6 and v7 generation SKUs for the D-family, none of which are supported by Databricks.

### Summary of Findings

| Aspect | Finding |
|--------|---------|
| Quota | 6 vCPUs total per region, non-increasable |
| SKUs available | Only v6/v7 in brazilsouth; only higher-cost families in eastus |
| SKUs supported by Databricks | Series v2, v3, v4 — none available |
| Region restriction | 5 regions allowed; no combination solves the problem |
| Databricks official position | Trial/free/student subscriptions are not supported for Databricks workloads |

The intersection between "SKUs available to this subscription" and "SKUs supported by Databricks" is **empty**.

---

## Decision

**Adopt local development for the data pipeline, keeping the Databricks Workspace provisioned as an infrastructure artifact.**

Specifically:

1. The Databricks Workspace remains provisioned in Terraform, with VNet Injection, SCC, and the `NoAzureDatabricksRules` configuration. This demonstrates the correct IaC provisioning of a production-grade Databricks environment.

2. The `databricks_cluster.pipeline` resource is **removed** from Terraform. It is documented as an intentional omission driven by the subscription limitation.

3. The data pipeline is implemented in Python with PySpark + Delta Lake, running locally, using the same code that would run on Databricks.

4. The pipeline includes:

   - API client for the BCB SGS API
   - Ingestion, validation, transformation, and persistence modules
   - A test suite with 10 tests, all passing
   - Setup automation via a shell script

5. The limitation is documented in this ADR, in the Phase 3 documentation, and in the project README.

---

## Consequences

### Positive

- **Portfolio narrative:** demonstrates the ability to make architectural decisions under real-world constraints, documenting trade-offs clearly
- **Code quality preserved:** the pipeline code is identical to what would run on Databricks, so the demonstration of data engineering skill is intact
- **Infrastructure demonstration:** the Databricks Workspace, VNet Injection, SCC, and NSG rules are all provisioned and visible in the Azure Portal
- **CI/CD readiness:** the Phase 4 pipelines will work regardless of the Databricks cluster being present

### Negative

- **No live Databricks execution:** the cluster is not available, so the pipeline does not execute on the cloud platform
- **No Unity Catalog demonstration:** the metastore requires a cluster to be initialized
- **No serverless integration:** features that depend on a running workspace (Jobs, Workflows, SQL Warehouses) cannot be demonstrated

### Mitigations

- The pipeline is executed and validated locally, with real data from the BCB
- The Databricks Workspace is provisioned and can be inspected
- The code is written to be portable: the same modules can be executed on Databricks without modification
- Future migration to a pay-as-you-go subscription would only require:

  1. Re-adding the `databricks_cluster` resource
  2. Running `terraform apply`
  3. Optionally deploying the notebooks via CLI

---

## Alternatives Considered

### Alternative A — Upgrade to Pay-As-You-Go

Not chosen. The project is intended as a portfolio demonstration and upgrading would incur real costs without clear additional value for the learning objectives.

### Alternative B — Use Databricks Community Edition

Not chosen. Community Edition runs on Databricks-managed infrastructure, so it does not demonstrate Azure integration, VNet Injection, or private networking. It would also not be compatible with the Terraform-provisioned workspace.

### Alternative C — Use Microsoft Fabric Trial

Not chosen. Fabric is a different platform with a different mental model. Adopting it would fragment the project narrative and require rewriting all documentation.

### Alternative D — Use another cloud (AWS or GCP)

Not chosen. The project is explicitly Azure-focused, aligned with the certification path and the professional objective.

---

## References

- Databricks documentation: VNet Injection requirements
- Databricks documentation: Supported node types
- Microsoft documentation: Azure for Students limitations
- Internal investigation logs: see `docs/phases/phase-2-databricks-data-lake.md` (Lessons Learned)
- Related phase: [Phase 3 — Data Pipeline](../phases/phase-3-pipeline.md)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-09-18 | Initial decision recorded |
