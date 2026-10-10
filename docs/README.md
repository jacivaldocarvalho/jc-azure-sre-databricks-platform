# Documentation

Central documentation for the JC-Azure SRE Databricks Platform project.

## Structure

| Directory | Purpose |
|-----------|---------|
| `phases/` | Detailed record of each project phase (what, why, how, validation) |
| `architecture/` | Architecture Decision Records (ADRs), security model, and diagrams |
| `operations/` | Runbooks, procedures, DR reference, and post-apply checklists |
| `troubleshooting/` | Guides for common issues and recovery |
| `conventions.md` | Project-wide standards and conventions |

## Overview Documents

- [Executive Summary](executive-summary.md) — 5-minute overview of the project
- [Roadmap Journey](roadmap-journey.md) — the story of how the project was built
- [Cost Analysis](operations/cost-analysis.md) — cost posture and FinOps practices

## Quick Links

### Phases

- [Phase 0 — Foundation](phases/phase-0-foundation.md)
- [Phase 1 — Base Network](phases/phase-1-network.md)
- [Phase 2 — Databricks and Data Lake](phases/phase-2-databricks-data-lake.md)
- [Phase 3 — Data Pipeline](phases/phase-3-pipeline.md)
- [Phase 4 — CI/CD with Azure DevOps](phases/phase-4-cicd.md)
- [Phase 5 — Observability](phases/phase-5-observability.md)
- [Phase 6 — Security](phases/phase-6-security.md)
- [Phase 7 — AI Integration](phases/phase-7-ai.md)
- [Phase 8 — AKS and Containerized Workloads](phases/phase-8-aks.md)
- [Phase 9 — Disaster Recovery](phases/phase-9-dr.md)
- [Phase 10 — Cost Optimization and Governance](phases/phase-10-governance.md)

### Architecture

- [Security Model](architecture/security-model.md) — reference document

### Architecture Decision Records

- [ADR-001 — Databricks Cluster Limitation in Azure for Students](architecture/adr-001-databricks-cluster-limitation.md)
- [ADR-002 — Observability Stack Selection](architecture/adr-002-observability-stack.md)
- [ADR-003 — Security Model Decisions](architecture/adr-003-security-model.md)
- [ADR-004 — AI Integration Strategy](architecture/adr-004-ai-integration.md)
- [ADR-005 — AKS Local-First Strategy](architecture/adr-005-aks-local-first.md)
- [ADR-006 — Disaster Recovery Strategy](architecture/adr-006-dr-strategy.md)
- [ADR-007 — Azure for Students Subscription](architecture/adr-007-azure-for-students.md)
- [ADR-008 — Three-Environment Structure](architecture/adr-008-three-environments.md)
- [ADR-009 — Terraform as Infrastructure as Code](architecture/adr-009-terraform.md)
- [ADR-010 — Network Topology](architecture/adr-010-network-topology.md)

### Operations

- [Operations README](operations/README.md) — day-to-day operations and post-apply checklist
- [Disaster Recovery Reference](operations/disaster-recovery.md) — RTO/RPO objectives and component inventory
- [DR Test Log](operations/dr-test-log.md) — record of executed DR tests

#### Runbooks

- [Recover Terraform State](operations/runbooks/recover-terraform-state.md)
- [Recover Key Vault Secret](operations/runbooks/recover-keyvault-secret.md)
- [Re-provision Environment](operations/runbooks/reprovision-environment.md)
- [Recover from Lost Machine](operations/runbooks/recover-from-lost-machine.md)

### Troubleshooting and Standards

- [Troubleshooting](troubleshooting/README.md) — common issues and fixes
- [Conventions](conventions.md) — project standards

## How to Use This Documentation

Each phase document follows a consistent structure:

1. **Objective** — what the phase set out to accomplish
2. **Context** — preconditions, dependencies, and decisions
3. **Implementation** — what was built and how
4. **Validation** — how to verify success
5. **Lessons Learned** — what changed and why
6. **Artifacts** — files, resources, and outputs produced

ADRs follow the Nygard pattern: Status, Context, Decision, Consequences, Alternatives, References.

The security model is a reference document, organized by asset inventory, threat model, identities, role assignments, authentication flows, and limitations.

The disaster recovery reference defines RTO/RPO objectives, criticality classification, and recovery strategies. It is complemented by the runbooks and the test log.

## Audience

- **Recruiters and technical interviewers** — to assess the depth of technical decisions
- **Engineers replicating the setup** — to follow the phases step by step
- **Future self** — to remember why certain choices were made

## Related Documentation

- [Main README](../README.md) — project overview and quick start
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute