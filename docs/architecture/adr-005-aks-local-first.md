# ADR-005 — AKS Local-First Strategy

**Status:** Accepted (with documented limitation)
**Date:** 2026-10-01
**Deciders:** Project author
**Context:** Phase 8 (AKS and Containerized Workloads)

---

## Context and Problem Statement

Phase 8 was designed to provision an Azure Kubernetes Service (AKS)
cluster and deploy a containerized workload on it. During planning, it
became clear that the current subscription cannot afford AKS due to
continuous costs, even when the cluster is idle.

This ADR captures the investigation, the alternatives considered, and the
final decision: **preserve the AKS Terraform module and demonstrate the
full stack locally with Kind**.

---

## The Cost Problem

Unlike all previous phases, AKS has **continuous cost even with zero nodes**:

| Component | Idle cost (30 days) | Notes |
|-----------|---------------------|-------|
| Load Balancer (Standard) | ~$18 USD | Created automatically, cannot be removed while the cluster exists |
| Azure Container Registry (Basic) | ~$5 USD | Needed to store the API image |
| Node pool (B2s, 1 node) | ~$30-40 USD | Only if provisioned; can be scaled to 0 |
| **Minimum without nodes** | **~$23 USD/month** | Just the LB and ACR |
| **Typical usage** | **~$50-70 USD/month** | With one active node |

The Azure for Students subscription has a total credit that has already
been consumed by Phases 1-7. Provisioning AKS would deplete the remaining
credit within weeks without producing lasting value for a portfolio.

Additional constraints:

- **Regional vCPU quota:** 6 vCPUs in the allowed regions.
- **Billing:** only the student credit is available; no Pay-As-You-Go.
- **Time:** the project is a portfolio demonstration, not a production
  workload. Continuous operation is not a requirement.

---

## Investigation: Options Considered

Five options were evaluated.

### Option A — Provision AKS, demonstrate, and destroy

Provision the cluster, run the demonstration, capture screenshots, and
destroy it immediately.

**Pros:** real AKS demo, low one-time cost (~$1-2 for a few hours).
**Cons:** the environment is not available to reviewers; screenshots must
be committed to the repo; the demonstration is one-shot.

### Option B — Kind local only, no AKS module

Use Kind exclusively. Do not create the AKS Terraform module.

**Pros:** zero cost, reproducible.
**Cons:** no artifact demonstrating AKS provisioning skill; less
impressive for a portfolio focused on Azure.

### Option C — Skip AKS entirely

Drop the phase and move to Phase 9.

**Pros:** saves time.
**Cons:** loses the opportunity to demonstrate Kubernetes competence.

### Option D — Local-first with preserved Terraform (chosen)

Create the full AKS Terraform module, validate it, but keep it commented
out. Use Kind for the actual demonstration, with the same manifests and
Helm charts that would run on AKS.

**Pros:** demonstrates both Kubernetes and AKS provisioning; zero cost;
reproducible by anyone cloning the repo; coherent with Phases 4 and 7.
**Cons:** the demonstration is not literally on AKS.

### Option E — AKS Automatic

Use the newer AKS Automatic SKU, which scales to zero automatically.

**Pros:** potentially cheaper when idle.
**Cons:** availability varies by subscription; still requires billing;
not yet supported by all regions; risk of unknown behavior.

### Comparison

| Option | Cost | Demonstrates K8s | Demonstrates AKS | Reproducible | Coherent |
|--------|------|------------------|------------------|--------------|----------|
| A | ~$1-2 | Yes (real) | Yes (real) | Partially | Medium |
| B | $0 | Yes | No | Yes | Medium |
| C | $0 | No | No | N/A | Low |
| **D** | **$0** | **Yes** | **Yes (as code)** | **Yes** | **High** |
| E | Variable | Yes | Yes | Medium | Medium |

---

## Decision

**Option D — Local-first with preserved Terraform.**

Two sub-decisions:

1. **Preserve the AKS Terraform module** in the repository, fully
   validated. It is commented out in the environment wiring but ready to
   activate with a one-line change.

2. **Use Kind for the demonstration.** The manifests, Helm charts,
   ServiceMonitor, and Grafana dashboards are identical to what would run
   on AKS. The only difference is the compute backend.

---

## Rationale

1. **Coherence with the project's pattern.** Phases 4 (CI/CD) and 7 (AI)
   already followed this pattern: code ready, execution limited by the
   subscription, documented in an ADR.

2. **Zero cost.** The entire demonstration runs on the local machine.

3. **Reproducibility.** Anyone cloning the repository can run
   `make kind-all` and see the full stack running in minutes.

4. **Honest.** The ADR documents the reasoning and the activation path
   for when a compatible subscription becomes available.

5. **Real Kubernetes.** Kind runs a genuine Kubernetes API server,
   scheduler, controller manager, and CNI. It is not a simulation.

---

## Architecture

### Local (current environment)

The diagram below shows what runs on the local machine with the Kind-based
setup.

```
   ┌────────────────────────────────────────────────────────────────┐
   │  HOST MACHINE (Ubuntu + Docker)                                │
   │                                                                │
   │   ┌────────────────────────────────────────────────────────┐   │
   │   │  Kind cluster: jc-sre-local                            │   │
   │   │  (Kubernetes node running as a Docker container)       │   │
   │   │                                                        │   │
   │   │   ┌────────────────────────────────────────────────┐   │   │
   │   │   │  Namespace: jc-sre                             │   │   │
   │   │   │                                                │   │   │
   │   │   │   ┌──────────────┐    ┌──────────────────┐    │   │   │
   │   │   │   │  Deployment  │    │  ServiceMonitor  │    │   │   │
   │   │   │   │  jc-sre-api  │    │  jc-sre-api      │    │   │   │
   │   │   │   │  (FastAPI)   │    │  (label selector)│    │   │   │
   │   │   │   └──────┬───────┘    └────────┬─────────┘    │   │   │
   │   │   │          │                     │              │   │   │
   │   │   │          │ /metrics            │ scrape       │   │   │
   │   │   │          ▼                     ▼              │   │   │
   │   │   │   ┌──────────────────────────────────────┐    │   │   │
   │   │   │   │  Prometheus                          │    │   │   │
   │   │   │   │  (kube-prometheus-stack)             │    │   │   │
   │   │   │   └──────────────┬───────────────────────┘    │   │   │
   │   │   │                  │                            │   │   │
   │   │   │                  ▼                            │   │   │
   │   │   │   ┌──────────────────────────────────────┐    │   │   │
   │   │   │   │  Grafana                             │    │   │   │
   │   │   │   │  Dashboard: "JC SRE API - Overview"  │    │   │   │
   │   │   │   └──────────────────────────────────────┘    │   │   │
   │   │   │                                                │   │   │
   │   │   │   ┌──────────────────────────────────────┐    │   │   │
   │   │   │   │  NGINX Ingress Controller            │    │   │   │
   │   │   │   │  Host: jc-sre.local                  │    │   │   │
   │   │   │   └──────────────────────────────────────┘    │   │   │
   │   │   │                                                │   │   │
   │   │   └────────────────────────────────────────────────┘   │   │
   │   │                                                        │   │
   │   │   Volume (extraMount):                                 │   │
   │   │     /data/spark-warehouse ← host: python/spark-warehouse│  │
   │   │                                                        │   │
   │   └────────────────────────────────────────────────────────┘   │
   │                                                                │
   │   ┌────────────────────────────────────────────────────────┐   │
   │   │  Docker daemon (host)                                  │   │
   │   │                                                        │   │
   │   │   jc-sre-databricks-api:latest                         │   │
   │   │   (built from python/Dockerfile)                       │   │
   │   │                                                        │   │
   │   └────────────────────────────────────────────────────────┘   │
   │                                                                │
   │   Port forwards (para acesso local):                           │
   │     localhost:8080 → jc-sre-api Service                         │
   │     localhost:3000 → Grafana                                    │
   │     localhost:9090 → Prometheus                                 │
   │                                                                │
   └────────────────────────────────────────────────────────────────┘
```

### Target (Azure AKS, when available)

The diagram below shows the same workload running on AKS. The manifests
and Helm charts are identical.

```
   ┌─────────────────────────────────────────────────────────────────┐
   │  AZURE SUBSCRIPTION                                             │
   │                                                                 │
   │   ┌─────────────────────────────────────────────────────────┐   │
   │   │  Resource Group: dev-sredatabricks-rg                   │   │
   │   │                                                         │   │
   │   │   ┌───────────────────────────────────────────────┐     │   │
   │   │   │  Virtual Network (10.0.0.0/16)                │     │   │
   │   │   │                                               │     │   │
   │   │   │   Subnet: aks (10.0.2.0/24)                   │     │   │
   │   │   │   ┌───────────────────────────────────────┐   │     │   │
   │   │   │   │  AKS cluster (dev-sredatabricks-aks)  │   │     │   │
   │   │   │   │  - Azure CNI + Calico policy          │   │     │   │
   │   │   │   │  - System node pool (0-2 nodes)       │   │     │   │
   │   │   │   │  - Workload node pool (0-3 nodes)     │   │     │   │
   │   │   │   │  - System-assigned managed identity   │   │     │   │
   │   │   │   │                                       │   │     │   │
   │   │   │   │   Namespace: jc-sre                   │   │     │   │
   │   │   │   │   ┌──────────────┐  ┌──────────────┐  │   │     │   │
   │   │   │   │   │  API pods    │  │  Prometheus  │  │   │     │   │
   │   │   │   │   │  (FastAPI)   │  │  Grafana     │  │   │     │   │
   │   │   │   │   └──────┬───────┘  └──────┬───────┘  │   │     │   │
   │   │   │   │          │                 │          │   │     │   │
   │   │   │   │          └────────┬────────┘          │   │     │   │
   │   │   │   │                   │                   │   │     │   │
   │   │   │   │                   ▼                   │   │     │   │
   │   │   │   │          ┌────────────────┐           │   │     │   │
   │   │   │   │          │  Azure Load    │           │   │     │   │
   │   │   │   │          │  Balancer      │           │   │     │   │
   │   │   │   │          └────────┬───────┘           │   │     │   │
   │   │   │   └──────────────────┬┘                   │   │     │   │
   │   │   └──────────────────────┼────────────────────┘   │     │   │
   │   │                          │                        │     │   │
   │   │   ┌──────────────────────┼────────────────────┐   │     │   │
   │   │   │  Azure Container Registry (ACR)           │   │     │   │
   │   │   │  - jc-sre-databricks-api:latest           │   │     │   │
   │   │   └────────────────────────────────────────────┘   │     │   │
   │   │                          │                         │     │   │
   │   │   ┌──────────────────────┼────────────────────┐   │     │   │
   │   │   │  Azure Monitor Workspace                  │   │     │   │
   │   │   │  - remote_write from in-cluster Prometheus│   │     │   │
   │   │   └───────────────────────────────────────────┘   │     │   │
   │   │                                                    │     │   │
   │   │   ┌────────────────────────────────────────────┐  │     │   │
   │   │   │  Key Vault (dev-sredatabricks-kv)          │   │     │   │
   │   │   │  - accessed via Workload Identity          │   │     │   │
   │   │   └────────────────────────────────────────────┘  │     │   │
   │   │                                                    │     │   │
   │   │   ┌────────────────────────────────────────────┐  │     │   │
   │   │   │  Data Lake Storage (devsredata)            │   │     │   │
   │   │   │  - accessed via CSI driver + Managed Ident.│   │     │   │
   │   │   └────────────────────────────────────────────┘  │     │   │
   │   │                                                    │     │   │
   │   └────────────────────────────────────────────────────┘     │   │
   │                                                              │   │
   └──────────────────────────────────────────────────────────────┘   │
                                                                      │
   Difference from Kind:                                               │
     - The node pool is provisioned and billed continuously.           │
     - The Load Balancer is provisioned by Azure when a Service of    │
     │   type LoadBalancer is created.                                 │
     - Storage is mounted via Azure Files CSI or Blob CSI.            │
     - Secrets come from Key Vault via the CSI driver.                │
   └───────────────────────────────────────────────────────────────────┘
```

---

## Consequences

### Positive

- **Zero cost.** The demonstration runs on the local machine.
- **Full Kubernetes stack.** Real API server, scheduler, controllers, CNI,
  network policies, RBAC, Ingress, Helm.
- **Reproducible.** Anyone cloning the repository can run the whole stack
  with `make kind-up`, `make kind-build`, `make kind-deploy`,
  `make kind-monitoring`.
- **Portable.** The Helm charts are identical to what runs on AKS.
- **Documented.** The activation procedure is documented in the phase and
  in this ADR.
- **Consistent with the project's pattern.** Aligns with Phases 4 and 7.

### Negative

- The AKS cluster is not provisioned. It exists only as Terraform code.
- The container image is stored in the local Docker daemon, not in ACR.
- The `LoadBalancer` Service type in Kind is emulated by port mappings,
  not by a real Azure Load Balancer.
- Secrets are read from the local filesystem, not from Key Vault.

### Mitigations

- The activation procedure is documented step-by-step.
- The Terraform module for AKS is validated.
- The Helm charts work identically in both environments.
- The README documents the limitation clearly.

---

## Alternatives Considered and Rejected

### AKS Automatic

Rejected because availability varies by subscription and the cost
model is still not free.

### Managed Kubernetes outside Azure (GKE, EKS)

Rejected because the project is explicitly Azure-focused.

### Minikube instead of Kind

Considered. Minikube is more mature and supports more features. Rejected
because Kind is lighter, runs entirely in Docker, and does not require
virtualization (KVM, VirtualBox). The choice between Kind and Minikube is
mostly a matter of preference; both are valid.

### K3s (lightweight Kubernetes)

Considered. K3s is closer to production-grade. Rejected because it requires
system-level installation and does not integrate as cleanly with Docker.

---

## References

- [Phase 8 — AKS and Containerized Workloads](../phases/phase-8-aks.md)
- [Phase 7 — AI Integration](../phases/phase-7-ai.md) — precedent for preserved modules
- [ADR-001 — Databricks Cluster Limitation](adr-001-databricks-cluster-limitation.md)
- [ADR-004 — AI Integration Strategy](adr-004-ai-integration.md)
- Kind documentation
- kube-prometheus-stack documentation
- NGINX Ingress Controller documentation

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-01 | Initial decision recorded |
