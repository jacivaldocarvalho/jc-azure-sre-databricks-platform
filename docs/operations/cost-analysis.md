# Cost Analysis

Reference document for the cost posture of the JC-Azure SRE Databricks Platform.

---

## Purpose

This document analyzes:

- The actual costs incurred during the project
- The theoretical costs if all planned resources were running
- The optimizations already in place
- The opportunities for further optimization
- The procedures for monitoring and controlling costs

The document is updated at the end of each phase and reviewed during
the quarterly audit.

---

## Context

### Azure for Students subscription

The project runs on an **Azure for Students** subscription
(`b4a10bfb-2a0e-43e7-bd50-ceb4624f160f`), which has:

- A fixed credit balance (typically $100 USD)
- No ability to add payment methods
- Restrictions on certain services and SKUs
- **No billing data exposed via the CLI** (`az consumption` returns
  `pretaxCost: None` for all records)
- **No budget API access** (`az consumption budget list` returns empty)

This shapes the entire cost strategy: the project is designed to keep
costs near zero, using local execution and destroying resources between
sessions.

### Strategy

The cost strategy follows three principles:

1. **Destroy after each session.** All resources can be destroyed with
   `make terraform-destroy`. Only the state backend is preserved.
2. **Local-first.** The data pipeline and Kubernetes workloads run
   locally. Only what cannot run locally is provisioned in Azure.
3. **Justify every resource.** Each resource in the Terraform code has a
   documented purpose. Resources that are preserved but not applied (AI,
   AKS) are commented out.

---

## Actual Costs Incurred

> **Note:** the Azure for Students subscription does not expose granular
> billing data through the CLI. The figures below are **estimates** based
> on resource usage and public pricing. They cannot be verified against
> the Azure Cost Management API in this subscription.

### Cost by service (cumulative, 2026-08 to 2026-10)

| Service | Usage | Estimated cost |
|---------|-------|----------------|
| Storage Account (ADLS Gen2) | ~5 MB stored, few transactions | < $0.01 |
| Key Vault | Few secret operations | < $0.01 |
| Application Insights | Few MB of metrics ingested | ~$0.10 |
| Log Analytics | Few MB of logs ingested | ~$0.10 |
| Azure Monitor Workspace | Provisioned, not used | $0.00 |
| Databricks Workspace (idle) | No cluster, no cost | $0.00 |
| Networking (VNet, NSG) | No egress beyond free tier | $0.00 |
| **Total estimate** | | **~$0.25** |

The project has been provisioned and destroyed multiple times across
phases. Each session has cost less than $0.01 in aggregate.

### Cost by phase

| Phase | Resources provisioned | Estimated cost |
|-------|----------------------|----------------|
| Phase 0 | None | $0.00 |
| Phase 1 | Networking | $0.00 |
| Phase 2 | + Storage, Databricks Workspace, Log Analytics | ~$0.05 |
| Phase 3 | No new resources (local pipeline) | $0.00 |
| Phase 4 | No new resources (CI/CD code only) | $0.00 |
| Phase 5 | + Application Insights, Azure Monitor Workspace | ~$0.10 |
| Phase 6 | + Key Vault | < $0.01 |
| Phase 7 | No new resources (AI module preserved) | $0.00 |
| Phase 8 | No new Azure resources (Kind local) | $0.00 |
| Phase 9 | No new resources (state protection) | < $0.01 |
| **Total** | | **~$0.25** |

### Cost of the state backend

The Terraform state backend (`tfstate-rg` + `tfstatejcsredatabricks`) is
the only resource that is **always active**. Its cost:

| Item | Cost |
|------|------|
| Storage Account (Standard_LRS) | ~$0.01/month |
| Blob versioning (300+ versions retained) | < $0.01/month |
| **Total** | **~$0.02/month** |

Even this can be considered negligible.

### Managed Resource Group (orphan, removed in Phase 10)

When the Databricks Workspace is destroyed, its **Managed Resource Group**
(`dev-sredatabricks-dbw-managed-rg`) is **not destroyed automatically**.
It is left orphaned, containing:

| Resource | Type | Purpose |
|----------|------|---------|
| `devsredatadbw` | Microsoft.Storage/storageAccounts | DBFS storage for the Databricks Workspace |
| `unity-catalog-access-connector` | Microsoft.Databricks/accessConnectors | Unity Catalog access connector |

**These resources were identified and removed in Phase 10** with:

```bash
az group delete --name dev-sredatabricks-dbw-managed-rg --yes --no-wait
```

**Impact:** the orphaned resources were consuming a small amount of
credit (the storage account, in particular, has a minimal monthly cost).
Removing them eliminates this residual cost.

**Lesson learned:** the Terraform configuration does not manage the
Managed Resource Group. When the Databricks Workspace is destroyed,
the managed group must be removed manually.

---

## Theoretical Costs (If Everything Were Running)

If all the planned resources were provisioned and running 24/7, the
monthly cost would be significantly higher. This section documents what
that would look like.

### AKS cluster (not provisioned)

| Component | Cost |
|-----------|------|
| Load Balancer (Standard) | ~$18/month |
| Azure Container Registry (Basic) | ~$5/month |
| Node pool (1 × Standard_B2s) | ~$30/month |
| **Total** | **~$53/month** |

This is why AKS is not provisioned. It would consume the credit in less
than 2 months.

### Databricks cluster (not provisionable)

| Component | Cost |
|-----------|------|
| Single-node cluster (Standard_DS3_v2) | ~$1.00/hour |
| At 2 hours/day | ~$60/month |
| **Total** | **~$60/month** |

This is why the pipeline runs locally. The same code runs in both
environments.

### Azure OpenAI (not provisionable)

| Component | Cost |
|-----------|------|
| GPT-4o-mini, ~1000 calls/month | < $0.50/month |

This is actually cheap. The limitation is quota, not cost. If quota
became available, the AI integration would cost less than $1/month at
the project's usage.

### Full production stack

If all the components were running in a production-like configuration:

| Component | Cost |
|-----------|------|
| AKS (2 nodes, Standard_B2ms) | ~$60/month |
| Azure Container Registry | $5/month |
| Databricks (auto-scaling, 2-8 workers) | $200-500/month |
| ADLS Gen2 (100 GB) | ~$2/month |
| Application Insights (high volume) | ~$20/month |
| Log Analytics (high volume) | ~$20/month |
| Azure OpenAI (moderate usage) | ~$10/month |
| Azure Monitor managed Prometheus | ~$5/month |
| **Total** | **~$320-620/month** |

**This is not what the project spends.** It is a reference to
understand the cost implications of the architectural choices.

---

## Optimizations Already in Place

The following practices keep costs near zero:

### 1. Local-first execution

The data pipeline runs locally. The FastAPI application runs on Kind.
Only the infrastructure that cannot run locally is provisioned in Azure.

**Impact:** saves ~$60-500/month compared to a cloud-based equivalent.

### 2. Destroy after each session

All Azure resources are destroyed with `make terraform-destroy` after
each session. The environment can be recreated in 15-25 minutes.

**Impact:** saves ~$50/month compared to keeping the environment running.

### 3. Preserved but not applied modules

The AI and AKS Terraform modules are validated but commented out. They
exist as code, ready to activate when the subscription allows.

**Impact:** saves ~$53/month (AKS) and potential cost for OpenAI usage.

### 4. Aggressive auto-termination

The Databricks cluster configuration (when applicable) uses auto-
termination in 30 minutes. The workspace itself does not incur cost
when idle.

**Impact:** limits the cost of a runaway cluster.

### 5. Local state backend

The Terraform state is stored in a single storage account with LRS
(locally redundant). GRS would double the cost for no benefit in a
single-region project.

**Impact:** saves ~$0.01/month. Small, but consistent with the principle.

### 6. No NAT Gateway

The VNet subnets use service endpoints and default outbound access.
A NAT Gateway would cost ~$32/month. It is not provisioned.

**Impact:** saves ~$32/month.

### 7. No Private Endpoints

Private Endpoints cost ~$7/month each, plus data processing. The
project uses service endpoints instead, which are free.

**Impact:** saves ~$7/month per endpoint (there are 3 planned).

### 8. Minimal Log Analytics retention

Log Analytics is configured with 30 days retention instead of 90 days
or more.

**Impact:** reduces storage cost by ~66% for logs.

### 9. Application Insights sampling

Application Insights uses 100% sampling (default for the project). In
production, adaptive sampling would reduce cost. Not needed at current
volume.

**Impact:** none at current volume.

### 10. Orphaned resources removed

The Managed Resource Group left orphaned by the Databricks Workspace was
removed in Phase 10. This eliminates the residual cost of the DBFS
storage account and the Unity Catalog connector.

**Impact:** eliminates a residual cost of < $0.01/month.

---

## Optimizations for the Future

The following optimizations are documented for when the project moves
to a paid subscription. They are **not applied now** because they would
either cost more or require resources that are not provisioned.

### When AKS is provisioned

| Optimization | Description | Estimated saving |
|--------------|-------------|------------------|
| Auto-scaling to 0 | Configure the node pool with `min_count = 0` | Up to 100% when idle |
| Spot instances | Use spot VMs for non-critical workloads | Up to 80% for the node cost |
| Reserved instances | Commit to 1-year or 3-year terms | Up to 40% |
| Right-sizing | Choose the smallest node that meets the need | Varies |

### When Databricks is used

| Optimization | Description | Estimated saving |
|--------------|-------------|------------------|
| Auto-scaling clusters | Min 0, max N workers | Up to 90% when idle |
| Spot instances for workers | Use spot for batch workloads | Up to 80% for worker cost |
| Cluster policies | Enforce max size, auto-termination | Prevents runaway costs |
| Photon only when needed | Photon costs more per DBU | 10-50% |
| Serverless SQL Warehouses | Pay per query, not per uptime | Varies |

### General optimizations

| Optimization | Description |
|--------------|-------------|
| Cost allocation tags | Tag every resource with `CostCenter` or `Owner` |
| Budget alerts | Set a budget and receive alerts when approaching it |
| Azure Advisor review | Periodic review of Azure Advisor recommendations |
| Azure Policy | Enforce tagging and SKU restrictions |

---

## Monitoring and Control

### How to check current cost

> **Note:** the Azure for Students subscription does not expose billing
> data via the CLI. The following commands return `None` or empty
> results. The portal must be used instead.

Via the portal:

1. Go to **Cost Management + Billing** > **Cost analysis**
2. Filter by subscription, resource group, or tag
3. Set the time range

Via CLI (returns `None` in the current subscription):

```bash
az consumption usage list \
  --start-date $(date -u -d '30 days ago' +%Y-%m-%d) \
  --end-date $(date -u +%Y-%m-%d) \
  --query "[].{Date:date, Cost:pretaxCost, Service:meterDetails.serviceName}" \
  -o table
```

### How to set a budget

> **Note:** budget creation is not exposed via the CLI in the Azure for
> Students subscription. The portal may offer limited functionality.

Via the portal (if available):

1. Go to **Cost Management + Billing** > **Budgets**
2. Click **Add**
3. Configure:
   - Amount: e.g., $5 USD
   - Reset period: monthly
   - Alert threshold: 50%, 80%, 100%
   - Email: the operator's address

### Routine cost review

Documented in `docs/operations/README.md` (section "FinOps Practices"):

- Weekly: check the credit balance in the portal
- Monthly: review this cost analysis
- Quarterly: audit the resources and the optimizations
- After each `terraform destroy`: verify that no orphaned resources remain

### Checking for orphaned resources

After each `terraform destroy`, verify that no resources are left behind:

```bash
# List all resource groups
az group list --query "[].{Name:name, Location:location}" -o table

# The only resource group that should remain is `tfstate-rg`
```

If the `dev-sredatabricks-dbw-managed-rg` appears, it is an orphan and
should be removed:

```bash
az group delete --name dev-sredatabricks-dbw-managed-rg --yes --no-wait
```

---

## Cost per Phase (Comparison)

A comparison of the cost of this project with typical alternatives:

| Approach | Monthly cost | Notes |
|----------|--------------|-------|
| **This project** | **< $0.03** | After destroy cycles |
| Cloud-only, minimal | ~$50 | All resources running, minimal |
| Cloud-only, production-like | ~$320-620 | AKS + Databricks + monitoring |
| Cloud-only, enterprise | $1,000+ | With HA, DR, compliance |

The project's cost strategy is at the extreme low end of the spectrum.
This is intentional, appropriate for the scope, and demonstrates FinOps
discipline.

---

## What Would Change with a Paid Subscription

If the project migrated to a Pay-As-You-Go subscription, the following
would become possible:

| Capability | Estimated monthly cost |
|-----------|-----------------------|
| Keep the environment running 24/7 | ~$50 |
| Provision a Databricks cluster (part-time) | ~$30 |
| Provision the AKS cluster | ~$53 |
| Use Azure OpenAI | < $1 |
| Enable Private Endpoints | ~$21 (3 endpoints) |
| Enable NAT Gateway | ~$32 |
| **Full production-like** | **~$187/month** |

This is not a recommendation. It is a reference to understand what the
current constraints save.

---

## Known Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| No Cost Management API access | Cannot programmatically query detailed billing | Use the portal; use estimates |
| No budget API access | Cannot automate cost alerts | Manual weekly review in the portal |
| No reserved instances | Cannot commit to long-term pricing | Accept the higher unit cost |
| No cost allocation tags | Cannot allocate cost by tag via API | Manual calculation |
| Managed Resource Group is not destroyed by Terraform | Orphaned resources accumulate after each destroy | Manually delete after each destroy |

---

## Action Items

- [x] Document the cost analysis in this reference
- [x] Identify and remove orphaned resources (Managed Resource Group)
- [ ] Add the orphan cleanup to the operations checklist (done in this phase)
- [ ] Review the cost analysis quarterly
- [ ] Consider budget configuration when a paid subscription is available

---

## Related Documents

- [Phase 10 — Cost Optimization and Governance](../phases/phase-10-governance.md)
- [ADR-007 — Azure for Students Subscription](adr-007-azure-for-students.md) (to be created)
- [Operations README](README.md) — routine checks
- [Security Model](../architecture/security-model.md) — governance context

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial cost analysis documented |
| 2026-10-09 | Updated with real subscription data and orphaned resource removal |
