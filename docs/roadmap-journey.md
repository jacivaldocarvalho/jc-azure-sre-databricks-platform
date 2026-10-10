# Roadmap Journey

The story of how the JC-Azure SRE Databricks Platform was built, phase
by phase.

---

## Purpose

This document tells the story of the project. It complements the
individual phase documents by showing the **arc** of the project:

- What was the goal at each phase?
- What changed during the execution?
- What decisions were made, and when?
- What was learned?

The phase documents focus on "what was built." This document focuses on
"how it evolved."

---

## The Arc of the Project

```
   Foundation ──▶ Network ──▶ Databricks ──▶ Pipeline ──▶ CI/CD
        │            │            │            │           │
        ▼            ▼            ▼            ▼           ▼
     Phase 0      Phase 1      Phase 2      Phase 3     Phase 4
        │            │            │            │           │
        │            │            │            │           │
        └────────────┴────────────┴────────────┴───────────┘
                                │
                                ▼
   ┌─────────────────────────────────────────────────────────┐
   │  Observability ──▶ Security ──▶ AI ──▶ Kubernetes ──▶ DR │
   │        │              │          │         │           │  │
   │        ▼              ▼          ▼         ▼           ▼  │
   │     Phase 5       Phase 6     Phase 7   Phase 8     Phase 9 │
   │                                                         │  │
   └─────────────────────────────────────────────────────────┘
                                │
                                ▼
                         ┌──────────────┐
                         │   Phase 10   │
                         │  Governance  │
                         └──────────────┘
```

---

## Phase 0 — Foundation

**Goal:** establish the base for the project.

**What was done:**
- Created the Git repository with a branching strategy
- Defined project conventions (naming, tagging, structure)
- Created the Makefile
- Set up `.env.example` and `.gitignore`

**What changed:** nothing significant. This was a clean phase.

**Key decision:** the three-environment structure (dev, staging, prod) — documented retroactively in ADR-008.

---

## Phase 1 — Base Network

**Goal:** provision the Azure network.

**What was done:**
- Set up the Terraform remote backend (Azure Storage)
- Created the `networking` module (VNet, subnets, NSG)
- Provisioned 5 subnets initially

**What changed:** later, a 6th subnet was added in Phase 2 (for Databricks private).

**Key decision:** single VNet with private endpoints (Option C) — documented retroactively in ADR-010.

**Lesson learned:** the `private_endpoint_network_policies_enabled` argument is deprecated in the AzureRM provider 4.x. This warning has been present since Phase 1 and remains documented as a future migration item.

---

## Phase 2 — Databricks and Data Lake

**Goal:** provision the Databricks Workspace and ADLS Gen2.

**What was done:**
- Databricks Workspace with VNet Injection
- ADLS Gen2 storage account with 4 containers
- Subnet delegation for Databricks

**What changed significantly:**
- The initial configuration used a `DenyAllInbound` NSG rule, which conflicted with the Databricks Network Intent Policy.
- Three iterations were needed:
  1. Default NSG with `DenyAllInbound` — failed
  2. `NoAzureDatabricksRules` without SCC — failed
  3. `NoAzureDatabricksRules` with SCC — succeeded
- The DBFS storage account name collided with the data lake account. Fixed by appending `dbw`.
- The `blob_properties.versioning_enabled` argument was incompatible with `is_hns_enabled = true`. Removed.

**Key decision:** adopt SCC and `NoAzureDatabricksRules` — documented in ADR-001 (cluster limitation) and referenced in the Security Model.

**Lesson learned:** always consult the managed service's networking requirements before applying restrictive defaults to its delegated subnets.

---

## Phase 3 — Data Pipeline

**Goal:** implement the data pipeline.

**What was done:**
- API client for the BCB SGS API with automatic chunking
- Ingestion, validation, transformation, persistence
- Delta Lake for storage
- 10 tests

**What changed:**
- The pipeline runs locally, not on Databricks. This was the first major adaptation to the constraints.
- The decision to run locally was documented in ADR-001.

**Lesson learned:** the same code works locally and in Databricks. The portability was intentional and validated.

---

## Phase 4 — CI/CD with Azure DevOps

**Goal:** automate validation and deployment.

**What was done:**
- Azure DevOps organization and project
- OIDC-based service connection (Workload Identity Federation)
- Terraform pipeline and Python pipeline
- Reusable YAML templates

**What changed significantly:**
- The pipelines could not run on Microsoft-hosted agents. Azure DevOps does not grant the free hosted parallel job to new organizations without billing, and Azure for Students is not accepted for billing.
- A self-hosted agent was considered and rejected (too fragile for a portfolio).
- The pipelines are preserved as code, ready to activate on a paid subscription.

**Key decision:** use OIDC instead of secrets. Documented in the phase.

**Lesson learned:** verify subscription eligibility before designing infrastructure that depends on it.

---

## Phase 5 — Observability

**Goal:** define SLIs/SLOs and implement observability.

**What was done:**
- SLIs and SLOs defined before choosing tools
- OpenTelemetry instrumentation across the pipeline
- Application Insights as the metrics backend
- Workbook `Pipeline Overview` with 5 panels
- Four SLO-aligned alert rules

**What changed significantly:**
- The original plan was to use managed Prometheus with Grafana. During implementation, it became clear that the official Microsoft SDK sends metrics to Application Insights, not to Prometheus.
- The decision was documented in ADR-002.

**Lesson learned:** the metrics backend is not interchangeable. Choose the backend first, then the SDK.

---

## Phase 6 — Security

**Goal:** adopt a least-privilege security posture.

**What was done:**
- Key Vault with RBAC authorization
- Application Insights secret migrated to Key Vault
- User-Assigned Managed Identity for Databricks
- Role assignments with least privilege
- Azure DevOps Service Principal scope reduced

**What changed significantly:**
- A legacy Service Principal from Phase 1 was identified and removed. It had Contributor at the subscription scope and an orphaned client secret.
- The `.env` still contained the legacy credentials, which caused `DefaultAzureCredential` to authenticate as the wrong identity.
- The `AZURE_USE_CLI=true` flag was introduced to force `AzureCliCredential` in local development.

**Key decision:** no long-lived secrets for service-to-service authentication. Documented in ADR-003.

**Lesson learned:** orphaned credentials are dangerous. Periodic audits are essential.

---

## Phase 7 — AI Integration

**Goal:** integrate AI into the pipeline.

**What was done:**
- Executive summary use case selected from 5 candidates
- AI client with fallback strategy
- Prompt templates
- Integration into the pipeline (Steps 5b and 6b)
- Delta persistence for summaries

**What changed significantly:**
- Azure OpenAI could not be provisioned due to quota restrictions.
- The Terraform module and Python client are preserved, ready to activate.
- The pipeline uses a deterministic fallback generator.

**Key decision:** preserve the module, implement a fallback. Documented in ADR-004.

**Lesson learned:** the subscription's constraints can block entire capabilities. Document them and provide alternatives.

---

## Phase 8 — Kubernetes

**Goal:** deploy a containerized workload on Kubernetes.

**What was done:**
- FastAPI application with 7 endpoints
- Multi-stage Dockerfile
- Kind cluster with NGINX Ingress
- Helm charts for the API and monitoring
- Prometheus + Grafana with a custom dashboard

**What changed significantly:**
- AKS could not be provisioned due to cost (Load Balancer ~$18/month).
- The Terraform module is preserved, validated, and ready to activate.
- The demonstration uses Kind, with identical Helm charts.

**Key decisions:**
- Local-first with preserved AKS module — documented in ADR-005.
- Use Kind + NGINX Ingress + kube-prometheus-stack.

**Lessons learned:**
- Kind's `hostPath` is not the host's filesystem. Use `extraMounts`.
- An overly aggressive `.helmignore` can prevent Helm from reading the chart.
- The Docker base image `python:3.12-slim` moved from Debian 12 to 13, replacing OpenJDK 17 with 21.

---

## Phase 9 — Disaster Recovery

**Goal:** define and validate a disaster recovery posture.

**What was done:**
- RTO/RPO objectives for all components
- Criticality classification (P0-P3)
- Backend protection (blob versioning, soft delete)
- Four runbooks
- Two DR tests executed successfully
- DR test log

**What changed significantly:**
- The Key Vault secret must be re-populated after every `terraform destroy` + `terraform apply`. This is documented in the Post-Apply Checklist.
- The `AzureCliCredential` first call may be slow. Documented.

**Key decision:** reproducibility-based DR. Documented in ADR-006.

**Lesson learned:** the DR strategy must align with the project's nature. Backing up what can be regenerated is wasted effort.

---

## Phase 10 — Cost Optimization and Governance

**Goal:** consolidate the project.

**What was done:**
- Cost analysis document
- FinOps practices documented
- Orphaned Managed Resource Group identified and removed
- Four retroactive ADRs (007-010)
- Executive summary
- Roadmap journey (this document)

**What changed significantly:**
- The Azure for Students subscription does not expose billing data via the CLI. Cost analysis uses estimates.
- The Databricks Managed Resource Group is not destroyed by Terraform. It must be removed manually.

**Lessons learned:**
- Orphaned resources accumulate silently.
- Retroactive ADRs are better than missing ADRs.

---

## Reflections

### What Went Well

- The project adapted to each constraint without compromising the original intent.
- Every limitation was documented with alternatives and reasoning.
- The code is portable (local / cloud), testable (15 tests), and versioned.
- The documentation is complete: 10 phases, 10 ADRs, 4 runbooks, and reference documents.

### What Was Difficult

- The subscription's constraints (regions, SKUs, billing) blocked several planned capabilities.
- Each adaptation required re-thinking the architecture, not just tweaking the code.
- Deciding what to preserve (as code) vs. what to remove was not always obvious.

### What Would Be Done Differently

- **Validate subscription eligibility before design.** Phases 4, 7, and 8 each discovered a limitation after the design was already done.
- **Test in the real environment sooner.** A small proof of concept for Databricks, AI, and AKS would have surfaced the limitations before the design phase.
- **Automate the Key Vault secret population.** It is a manual step after every apply. It could be a script.

### What Was Learned

- **Constraints are opportunities.** The project demonstrates more maturity than if it had unlimited resources.
- **Documentation is a deliverable.** The ADRs and phase documents are as valuable as the code.
- **Honesty is a feature.** Documenting what did not work is more impressive than hiding it.
- **Reproducibility is a superpower.** Because everything is code, the entire environment can be rebuilt in 30 minutes.

---

## The Result

The project is not a production system. It is a **portfolio piece** that
demonstrates:

- Technical depth across multiple domains
- Ability to adapt to constraints
- Discipline in documentation and testing
- Honesty about limitations

These are the qualities that distinguish a senior engineer from a
beginner. The project is an attempt to demonstrate them.

---

## Related Documents

- [Executive Summary](executive-summary.md)
- [Phases](phases/) — the individual phase documents
- [ADRs](architecture/) — the decision records
- [Cost Analysis](operations/cost-analysis.md)
- [Security Model](architecture/security-model.md)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial roadmap journey |