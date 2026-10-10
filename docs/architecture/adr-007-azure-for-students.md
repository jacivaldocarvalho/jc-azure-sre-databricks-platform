# ADR-007 — Azure for Students Subscription

**Status:** Accepted
**Date:** 2026-10-09 (recorded retroactively; decision made in Phase 0)
**Deciders:** Project author
**Context:** Phase 0 (Foundation)

---

## Context and Problem Statement

The project needs an Azure subscription to host the infrastructure and
demonstrate SRE/DevOps practices. Several subscription types are
available:

- Pay-As-You-Go (paid, no restrictions)
- Enterprise Agreement (via employer)
- Cloud Solution Provider (via reseller)
- Visual Studio Enterprise (via employer)
- Azure for Students (limited credit)
- Free Trial (limited credit, time-limited)

Which subscription type should be used?

---

## Options Considered

| Option | Description | Trade-offs |
|--------|-------------|------------|
| Pay-As-You-Go | Full Azure, paid | Requires a credit card and ongoing payment |
| Enterprise Agreement | Via employer | Not available for personal projects |
| Cloud Solution Provider | Via reseller | Not applicable |
| Visual Studio Enterprise | Via employer | Not available for personal projects |
| **Azure for Students** | Limited credit, student verification required | Free, but restrictive |
| Free Trial | Limited credit, 30-day window | Time-limited |

---

## Decision

Use **Azure for Students**.

---

## Rationale

1. **No cost.** The subscription provides a credit balance (typically
   $100 USD) with no payment method required.

2. **Realistic constraints.** The project is a portfolio, not a
   production system. The restrictions imposed by the subscription
   (limited credit, region policy, SKU restrictions) are realistic
   constraints that SREs face in enterprise environments.

3. **Authentic demonstration.** Working within constraints demonstrates
   more maturity than working with unlimited resources. The project
   documents every limitation and the alternatives considered.

4. **Accessibility.** The subscription is available to any student with
   a valid academic email, making the project reproducible by others.

---

## Consequences

### Positive

- **Zero cost.** The credit is sufficient for the project's usage
  (~$0.25 across the entire project).
- **Realistic constraints.** The limitations shape the architecture
  in a way that mirrors enterprise environments.
- **Reproducibility.** Anyone with a student email can reproduce the
  project.

### Negative

- **Restricted regions.** The policy `sys.regionrestriction` limits
  deployment to 5 regions. This affects SKU availability.
- **Restricted SKUs.** Some SKUs are not available for the subscription.
  This is why Databricks clusters and AKS cannot be provisioned.
- **Limited vCPU quota.** The total regional vCPU quota is 6 vCPUs.
  This is insufficient for a Databricks cluster.
- **No billing API access.** The CLI returns `pretaxCost: None` for all
  records. Cost analysis must be done via the portal.
- **No budget API access.** Budgets cannot be configured via the CLI.
- **No reserved instances.** Long-term pricing is not available.

### Mitigations

- The project documents every limitation in an ADR (001, 004, 005).
- Where possible, alternatives are provided (local execution, Kind).
- The `cost-analysis.md` document explains the constraints and provides
  estimates.

---

## Alternatives Considered and Rejected

### Pay-As-You-Go

Rejected because the project is a portfolio and the author does not
want to incur costs. The value of the project does not justify a
recurring expense.

### Free Trial

Rejected because it is time-limited (30 days) and would require the
project to be completed within that window. The project spans multiple
months.

### Multiple subscriptions

Rejected because managing multiple student subscriptions would add
complexity without a clear benefit.

---

## References

- [ADR-001 — Databricks Cluster Limitation](adr-001-databricks-cluster-limitation.md)
- [ADR-004 — AI Integration Strategy](adr-004-ai-integration.md)
- [ADR-005 — AKS Local-First Strategy](adr-005-aks-local-first.md)
- [Cost Analysis](../operations/cost-analysis.md)
- Microsoft documentation: Azure for Students subscription

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial decision recorded (retroactive) |
