# ADR-010 — Network Topology (Single VNet with Private Endpoints)

**Status:** Accepted
**Date:** 2026-10-09 (recorded retroactively; decision made in Phase 1)
**Deciders:** Project author
**Context:** Phase 1 (Base Network)

---

## Context and Problem Statement

The project requires a network topology that:

- Supports the Databricks Workspace with VNet Injection
- Segments workloads appropriately
- Balances security and complexity
- Fits the constrained budget

Three common topologies are available:

- Single VNet (simple)
- Hub-Spoke (standard for enterprises)
- Single VNet with Private Endpoints (balanced)

---

## Options Considered

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A — Single VNet | One VNet, all subnets together | Simple; less secure |
| B — Hub-Spoke | Central hub with peering to spokes | Complex; more secure; production-grade |
| C — Single VNet with Private Endpoints | One VNet, segmented, PaaS via private endpoints | Balanced |

---

## Decision

Adopt **Option C — Single VNet with Private Endpoints**.

---

## Rationale

1. **Segmentation.** The VNet has 6 subnets, each with a clear purpose:

   | Subnet | CIDR | Purpose |
   |--------|------|---------|
   | databricks | 10.0.1.0/24 | Databricks public subnet (delegated) |
   | aks | 10.0.2.0/24 | AKS cluster nodes |
   | data | 10.0.3.0/24 | Data services |
   | monitoring | 10.0.4.0/24 | Prometheus and Grafana |
   | private_endpoints | 10.0.5.0/24 | Private endpoints for PaaS |
   | databricks_private | 10.0.6.0/24 | Databricks private subnet (delegated) |

2. **Private Endpoints.** The dedicated subnet for private endpoints
   allows PaaS services (Storage, Key Vault) to be accessed privately.
   This is a security best practice and demonstrates awareness of
   network security.

3. **Simplicity.** Compared to hub-spoke, the topology is simpler.
   There is no need for peering, route tables, or a central hub.

4. **Fit to budget.** Private Endpoints cost ~$7/month each. The
   project's cost analysis includes this. In the current environment,
   service endpoints are used instead (free). Private Endpoints would
   be enabled in a paid subscription.

5. **Service endpoints.** The subnets use service endpoints for Storage
   and Key Vault, which are free and provide basic security.

---

## Consequences

### Positive

- **Segmentation.** Each workload has its own subnet.
- **Security.** Private endpoints (when enabled) provide private access
  to PaaS.
- **Simplicity.** No peering, no hub, no route tables.
- **Cost.** Service endpoints are free; private endpoints are optional.
- **Fit to budget.** The topology fits within the constrained budget.

### Negative

- **Not enterprise-standard.** Hub-spoke is the standard in many
  enterprises. The single VNet is simpler but less extensible.
- **Private Endpoints not enabled.** In the current environment, the
  private endpoints are not provisioned (cost). Service endpoints are
  used instead.
- **DNS configuration.** Private Endpoints require DNS configuration
  (private DNS zones). This is documented but not implemented.

### Mitigations

- The topology can be extended to hub-spoke in a future phase if
  needed.
- The private endpoints subnet exists and is ready.
- The ADR documents the reasoning.

---

## Alternatives Considered and Rejected

### Option A — Single VNet (without private endpoints)

Rejected because it lacks the segmentation and security of private
endpoints. The difference in cost is negligible (service endpoints
are free; private endpoints are ~$7/month each and not provisioned).

### Option B — Hub-Spoke

Rejected because it is over-engineered for a portfolio project. The
complexity (peering, route tables, hub with firewall) is not justified
by the scope.

### Multiple VNets without peering

Rejected because it would isolate workloads unnecessarily. Service
endpoints and private endpoints provide the required isolation without
separate VNets.

---

## References

- [Phase 1 — Base Network](../phases/phase-1-network.md)
- [Phase 2 — Databricks and Data Lake](../phases/phase-2-databricks-data-lake.md)
- [Security Model](security-model.md)
- [ADR-001 — Databricks Cluster Limitation](adr-001-databricks-cluster-limitation.md)
- Microsoft documentation: Azure Virtual Network topologies

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial decision recorded (retroactive) |
