# Architecture

Central index for architecture documentation, decisions, and diagrams for the JC-Azure SRE Databricks Platform.

---

## Purpose

This directory captures the architectural decisions that shape the project. It exists to answer three questions:

1. **What** architectural decisions were made?
2. **Why** were they made, and what alternatives were considered?
3. **What are the consequences** of each decision?

The format follows the lightweight ADR (Architecture Decision Record) pattern popularized by Michael Nygard: short, focused, immutable documents that capture the reasoning at the time of decision.

---

## Architecture Decision Records (ADRs)

| ID | Title | Status | Date |
|----|-------|--------|------|
| [ADR-001](adr-001-databricks-cluster-limitation.md) | Databricks Cluster Limitation in Azure for Students | Accepted | 2026-09-18 |
| [ADR-002](adr-002-observability-stack.md) | Observability Stack Selection | Accepted | 2026-09-24 |
| [ADR-003](adr-003-security-model.md) | Security Model Decisions | Accepted | 2026-09-26 |
| [ADR-004](adr-004-ai-integration.md) | AI Integration Strategy | Accepted | 2026-09-27 |
| [ADR-005](adr-005-aks-local-first.md) | AKS Local-First Strategy | Accepted | 2026-10-01 |
| [ADR-006](adr-006-dr-strategy.md) | Disaster Recovery Strategy | Accepted | 2026-10-09 |
| [ADR-007](adr-007-azure-for-students.md) | Azure for Students Subscription | Accepted (retroactive) | 2026-10-09 |
| [ADR-008](adr-008-three-environments.md) | Three-Environment Structure | Accepted (retroactive) | 2026-10-09 |
| [ADR-009](adr-009-terraform.md) | Terraform as Infrastructure as Code | Accepted (retroactive) | 2026-10-09 |
| [ADR-010](adr-010-network-topology.md) | Network Topology (Single VNet with Private Endpoints) | Accepted (retroactive) | 2026-10-09 |

### Retroactive ADRs

The ADRs 007 to 010 were recorded **retroactively** in Phase 10. They document decisions made in earlier phases (Phase 0 and Phase 1) that had not been captured at the time.

This consolidation ensures that the ADR log is complete and that every significant architectural decision is documented with alternatives, rationale, and consequences. See [Phase 10 — Cost Optimization and Governance](../phases/phase-10-governance.md) for the reasoning behind the retroactive documentation.

### Status Definitions

| Status | Meaning |
|--------|---------|
| **Proposed** | The decision is under consideration |
| **Accepted** | The decision has been made and is in effect |
| **Accepted (retroactive)** | The decision was made earlier but documented later |
| **Deprecated** | The decision is no longer relevant |
| **Superseded** | The decision has been replaced by a newer ADR |

---

## Reference Documents

Beyond the ADRs, this directory also contains reference documents that describe the current state of the architecture without proposing decisions:

| Document | Purpose |
|----------|---------|
| [Security Model](security-model.md) | Asset inventory, threat model, identities, role assignments, authentication flows |

---

## Principles Guiding Architectural Decisions

The following principles have been applied consistently:

### 1. Infrastructure as Code First

Every cloud resource is declared in Terraform. No manual provisioning, except for resources that are explicitly documented as exceptions (such as the Terraform state backend, which must exist before Terraform can run).

### 2. Simplicity Before Complexity

When multiple solutions exist, the simpler one is preferred unless the more complex option unlocks demonstrable value. This is why hub-spoke networking was rejected in favor of a single VNet with private endpoints (see [ADR-010](adr-010-network-topology.md)).

### 3. Security by Default

- Least privilege for RBAC
- No public blob access
- TLS 1.2 minimum
- Secure Cluster Connectivity for Databricks
- NSG with restrictive default posture and documented exceptions
- No long-lived secrets for service-to-service authentication

### 4. Testability and Portability

Business logic lives in libraries, not in notebooks or scripts. This makes the code testable locally, portable to Databricks, and independent of the execution environment.

### 5. Observability from the Start

Every meaningful component must be observable: structured logs, meaningful metrics, and clear alerts. This is planned from Phase 5 onward but is considered a first-class requirement in every prior phase.

### 6. Cost Awareness

The project runs on a constrained budget. Decisions must consider the cost implications. Resources not actively used are destroyed. This is reflected in the aggressive auto-termination settings, the choice of low-cost SKUs, and the local execution of the data pipeline. See [ADR-007](adr-007-azure-for-students.md) for the subscription context.

### 7. Document Decisions When They Happen

Architectural decisions are recorded while the context is fresh. This is why ADR-001 (Databricks limitation) was written in Phase 3, and ADR-004 (AI strategy) was written immediately after the quota limitation was discovered in Phase 7.

When a decision is made and later recognized as undocumented, it is recorded retroactively (as with ADRs 007-010). Recording late is better than not recording at all.

### 8. Honest Documentation of Limitations

When a decision is constrained by the platform or the environment, the constraint is documented explicitly and the alternatives are recorded. This is why ADR-001, ADR-002, ADR-004, ADR-005, and ADR-007 all include a "Consequences" section that names both what is gained and what is lost.

### 9. Reproducibility over Redundancy

When possible, the project prefers to regenerate resources from code rather than to back them up. This is why the data pipeline can re-fetch data from the BCB API, and the infrastructure can be re-provisioned from Terraform. See [ADR-006](adr-006-dr-strategy.md).

---

## Structure

```
docs/architecture/
├── README.md                                  # This file
├── security-model.md                          # Reference document
├── adr-001-databricks-cluster-limitation.md
├── adr-002-observability-stack.md
├── adr-003-security-model.md
├── adr-004-ai-integration.md
├── adr-005-aks-local-first.md
├── adr-006-dr-strategy.md
├── adr-007-azure-for-students.md
├── adr-008-three-environments.md
├── adr-009-terraform.md
└── adr-010-network-topology.md
```

---

## How to Read an ADR

Each ADR follows the same structure:

- **Status** — Proposed, Accepted, Deprecated, or Superseded
- **Context** — What problem are we solving?
- **Decision** — What did we decide to do?
- **Consequences** — What becomes easier or harder?
- **Alternatives Considered** — What else did we look at, and why did we reject it?
- **References** — Links to supporting material

The point is not to convince the reader that a decision was correct. The point is to make the decision transparent so that it can be revisited later with full context.

---

## ADRs by Theme

For easier navigation, the ADRs are grouped below by theme:

### Subscription and Constraints

- [ADR-001](adr-001-databricks-cluster-limitation.md) — Databricks Cluster Limitation
- [ADR-004](adr-004-ai-integration.md) — AI Integration Strategy
- [ADR-005](adr-005-aks-local-first.md) — AKS Local-First Strategy
- [ADR-007](adr-007-azure-for-students.md) — Azure for Students Subscription

These four ADRs are interconnected: they document how the subscription's constraints shaped the architecture and the alternatives adopted.

### Architecture and Networking

- [ADR-008](adr-008-three-environments.md) — Three-Environment Structure
- [ADR-009](adr-009-terraform.md) — Terraform as Infrastructure as Code
- [ADR-010](adr-010-network-topology.md) — Network Topology

These three ADRs document the foundational architectural decisions made in Phase 0 and Phase 1.

### Operations and Observability

- [ADR-002](adr-002-observability-stack.md) — Observability Stack Selection
- [ADR-003](adr-003-security-model.md) — Security Model Decisions
- [ADR-006](adr-006-dr-strategy.md) — Disaster Recovery Strategy

These three ADRs document the operational posture of the project.

---

## Related Documentation

- [Phases](../phases/) — chronological record of what was implemented
- [Conventions](../conventions.md) — standards applied across the project
- [Operations](../operations/) — runbooks and procedures
- [Troubleshooting](../troubleshooting/) — guides for common issues
- [Cost Analysis](../operations/cost-analysis.md) — cost posture and FinOps practices