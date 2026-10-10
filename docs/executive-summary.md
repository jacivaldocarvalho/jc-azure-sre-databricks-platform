# Executive Summary

High-level overview of the JC-Azure SRE Databricks Platform project.

---

## What This Project Is

A **portfolio project** that demonstrates SRE and DevOps practices applied
to a realistic Azure data platform. It integrates:

- Infrastructure as Code (Terraform)
- Data engineering (PySpark + Delta Lake)
- Observability (SLIs/SLOs, Application Insights, Prometheus)
- Security (Key Vault, Managed Identity, RBAC, no secrets)
- Containerized workloads (FastAPI on Kubernetes)
- AI integration (executive summaries with fallback)
- Disaster recovery (RTO/RPO, runbooks, tests)

The project is honest about its scope: it is not a production platform,
and it documents every limitation with the reasoning and the alternatives
considered.

---

## Why It Exists

Two motivations:

1. **Demonstrate competence.** The project serves as a portfolio piece
   for SRE/DevOps roles, showing hands-on experience with the tools and
   practices that enterprises use.

2. **Document the journey.** The project is not just code. It is a
   recorded process of decision-making, including what was attempted,
   what failed, and what was adapted. The ADRs and phase documentation
   capture this journey.

---

## What Was Delivered

| Component | Status |
|-----------|--------|
| Terraform infrastructure (8 modules) | Complete |
| Network segmentation (VNet, 6 subnets, NSG) | Complete |
| Databricks Workspace (VNet Injection, SCC) | Complete |
| Data pipeline (PySpark + Delta Lake) | Complete |
| Observability (SLIs/SLOs, alerts) | Complete |
| Security (Key Vault, Managed Identity, RBAC) | Complete |
| AI integration (with fallback) | Complete |
| Kubernetes workloads (Kind) | Complete |
| Disaster recovery (RTO/RPO, runbooks, tests) | Complete |
| CI/CD pipelines (Azure DevOps) | Code ready, execution blocked |
| Databricks cluster | SKU not available |
| Azure OpenAI | Code ready, quota not available |
| AKS cluster | Module preserved, not applied |

---

## How It Was Built

The project was executed in 10 phases, each documented in
`docs/phases/`. The phases were:

| Phase | Focus | Result |
|-------|-------|--------|
| 0 | Foundation | Git, Makefile, conventions |
| 1 | Base Network | VNet, subnets, NSG |
| 2 | Databricks and Data Lake | Workspace + ADLS Gen2 |
| 3 | Data Pipeline | PySpark + Delta, 15 tests |
| 4 | CI/CD | YAML pipelines, OIDC |
| 5 | Observability | SLIs/SLOs, Application Insights |
| 6 | Security | Key Vault, Managed Identity, RBAC |
| 7 | AI Integration | Summaries with fallback |
| 8 | Kubernetes | FastAPI on Kind, Prometheus, Grafana |
| 9 | Disaster Recovery | RTO/RPO, runbooks, backend protection |
| 10 | Governance | Cost analysis, retroactive ADRs |

Each phase followed a consistent structure:

- **Objective:** what the phase set out to accomplish
- **Context:** preconditions and dependencies
- **Implementation:** what was built and how
- **Validation:** how to verify success
- **Lessons Learned:** what changed and why
- **Artifacts:** files, resources, and outputs

---

## The Constraints That Shaped It

The project runs on an **Azure for Students** subscription, which has:

- A fixed credit balance
- Restricted regions (5 allowed)
- Restricted SKUs
- A 6-vCPU regional quota
- No billing API access

These constraints shaped the architecture:

| Constraint | Architectural Response |
|-----------|------------------------|
| No Databricks cluster | Pipeline runs locally with the same code |
| No Azure OpenAI | Fallback generator for summaries |
| No AKS cluster | Kind for local Kubernetes |
| No billing API | Cost estimates in `cost-analysis.md` |
| Limited vCPU quota | Local-first execution for everything possible |

Every constraint is documented in an ADR with alternatives considered.

---

## What Makes It Different

Most SRE portfolios show isolated pieces: a Terraform file, a CI/CD
pipeline, a dashboard. This project integrates them.

Most portfolios hide limitations. This project documents them.

Most portfolios stop at "it works." This project goes further:

- **Decision records** (10 ADRs) explain every significant choice.
- **Phase documentation** (10 documents) chronicles the journey.
- **Operational runbooks** (4 documents) enable recovery.
- **DR test log** records what was tested and what was not.
- **Cost analysis** shows the financial discipline behind the choices.

The result is not just a working project. It is a **demonstration of
engineering maturity**.

---

## How to Navigate the Documentation

### If you have 5 minutes

Read this document and the [main README](../README.md).

### If you have 30 minutes

Read the [main README](../README.md), then the [Phase 3 — Data Pipeline](phases/phase-3-pipeline.md)
and the [Security Model](architecture/security-model.md).

### If you have 2 hours

Read the 10 phases in order, then the 10 ADRs, then the operations
documentation.

### If you want to replicate the project

Follow the [Quick Start](../README.md#quick-start) and consult the
[Operations README](operations/README.md) for day-to-day commands.

### If you want to understand a specific decision

Look in the [ADRs by Theme](architecture/README.md#adrs-by-theme) for
the relevant topic.

---

## What's Not in This Project

The project is honest about what it is **not**:

- It is not a production system. Production requires HA, DR at scale,
  compliance, and 24/7 operations.
- It is not a multi-region deployment. It runs in a single Azure region.
- It is not a streaming platform. The pipeline is batch-oriented.
- It is not an ML platform. The AI integration is a demonstration.
- It is not a large-scale Kubernetes deployment. Kind is single-node.

These limitations are documented. They are not failures; they are
deliberate scope decisions appropriate for a portfolio project.

---

## Contact

**Jacivaldo Carvalho**
Telecommunications Engineer | DevOps | SRE | Networking

GitHub: [jacivaldocarvalho](https://github.com/jacivaldocarvalho)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial executive summary |