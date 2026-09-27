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
| [ADR-004](adr-004-ai-integration.md) | AI Integration Strategy | Accepted (with documented limitation) | 2026-09-27 |

### Planned ADRs

The following ADRs will be created as the project progresses through the remaining phases:

| ID | Title | Target Phase |
|----|-------|--------------|
| ADR-005 | AKS cluster configuration and workload deployment | Phase 8 |
| ADR-006 | Disaster recovery strategy | Phase 9 |
| ADR-007 | Cost optimization and governance | Phase 10 |

The following retroactive ADRs may be added for completeness:

| ID | Title | Reference Phase |
|----|-------|-----------------|
| ADR-008 | Network topology: single VNet with private endpoints | Phase 1 |
| ADR-009 | Selection of Azure for Students and its implications | Phase 0 |

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

When multiple solutions exist, the simpler one is preferred unless the more complex option unlocks demonstrable value. This is why hub-spoke networking was rejected in favor of a single VNet with private endpoints.

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

The project runs on a constrained budget. Decisions must consider the cost implications. Resources not actively used are destroyed. This is reflected in the aggressive auto-termination settings, the choice of low-cost SKUs, and the local execution of the data pipeline.

### 7. Document Decisions When They Happen

Architectural decisions are recorded while the context is fresh. This is why ADR-001 (Databricks limitation) was written in Phase 3, and ADR-004 (AI strategy) was written immediately after the quota limitation was discovered in Phase 7.

### 8. Honest Documentation of Limitations

When a decision is constrained by the platform or the environment, the constraint is documented explicitly and the alternatives are recorded. This is why ADR-001, ADR-002, and ADR-004 all include a "Consequences" section that names both what is gained and what is lost.

---

## Structure

```
docs/architecture/
├── README.md                                  # This file
├── security-model.md                          # Reference document
├── adr-001-databricks-cluster-limitation.md
├── adr-002-observability-stack.md
├── adr-003-security-model.md
└── adr-004-ai-integration.md
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

## Related Documentation

- [Phases](../phases/) — chronological record of what was implemented
- [Conventions](../conventions.md) — standards applied across the project
- [Operations](../operations/) — runbooks and procedures
- [Troubleshooting](../troubleshooting/) — guides for common issues
