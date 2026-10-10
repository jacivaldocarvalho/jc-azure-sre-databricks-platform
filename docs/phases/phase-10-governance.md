# Phase 10 — Cost Optimization and Governance

**Status:** Completed
**Duration:** Multi-iteration (cost analysis, FinOps practices, retroactive ADRs, consolidation)
**Dependencies:** Phase 9 (Disaster Recovery)

---

## Objective

Consolidate the project by:

- Analyzing the cost posture of the platform
- Documenting FinOps practices and optimizations
- Recording retroactive ADRs for decisions made in earlier phases
- Providing an executive summary and a roadmap journey
- Officially closing the roadmap

This is the **final phase** of the project. Its purpose is not to add
new capabilities, but to close the existing ones coherently.

---

## Context

### Why a governance phase

After nine phases of technical work, the project had:

- 8 Terraform modules
- 15 passing tests
- A documented security model
- A tested DR strategy
- Multiple ADRs
- 9 phase documents

What was missing was **coherence at the top level**:

- A document that summarizes the project for a non-technical audience
- A document that tells the story of the project
- A cost analysis that explains the financial discipline
- ADRs for decisions made in earlier phases

The governance phase addresses these gaps.

### Constraints

| Constraint | Impact |
|-----------|--------|
| Azure for Students | No billing API, no budget API |
| Orphaned resources | Managed Resource Group not destroyed by Terraform |
| Portfolio scope | Documentation is the primary deliverable |

---

## Implementation

### 1. Cost Analysis

Created `docs/operations/cost-analysis.md` with:

- **Actual costs:** estimated at ~$0.25 across the project
- **Cost by service:** Storage, Key Vault, Application Insights, Log Analytics
- **Cost by phase:** each phase's incremental cost
- **Theoretical costs:** what the project would cost with a paid subscription
- **Optimizations in place:** 10 practices that keep costs near zero
- **Optimizations for the future:** what to do when the subscription upgrades
- **Known limitations:** no billing API, no budget API
- **Action items:** included in the operations checklist

**Key insight:** the Azure for Students subscription does not expose
billing data via the CLI. Cost analysis is based on estimates.

### 2. FinOps Practices

Added a "FinOps Practices" section to `docs/operations/README.md`:

- Five principles (destroy after each session, local-first, verify after
  destroy, document every resource, cheapest tier)
- **Orphaned resources procedure:** after `terraform destroy`, always
  verify that the Managed Resource Group from Databricks was removed
- Cost monitoring via the portal
- Recommendations for a paid subscription

**Key insight:** the Managed Resource Group (`dev-sredatabricks-dbw-managed-rg`)
was found orphaned after Phase 9's destroy. It was removed in Phase 10.

### 3. Retroactive ADRs

Created four ADRs to document decisions made in earlier phases:

| ADR | Title | Reference Phase |
|-----|-------|-----------------|
| ADR-007 | Azure for Students Subscription | Phase 0 |
| ADR-008 | Three-Environment Structure | Phase 0 |
| ADR-009 | Terraform as Infrastructure as Code | Phase 0 |
| ADR-010 | Network Topology (Single VNet with Private Endpoints) | Phase 1 |

These ADRs document the foundational decisions that shaped the project.
Recording them retroactively is better than leaving them undocumented.

### 4. Consolidation Documents

Created two documents to close the roadmap:

- **`docs/executive-summary.md`** — a 5-minute overview for
  non-technical readers (recruiters, managers, coordinators)
- **`docs/roadmap-journey.md`** — the story of the project, from
  Phase 0 to Phase 10, including what changed at each phase

Updated `docs/architecture/README.md` with:

- The complete ADR index (10 ADRs)
- The "Retroactive ADRs" section
- The "ADRs by Theme" section for easier navigation

### 5. Tagging Verification

Verified that all modules apply tags consistently:

- networking: VNet, NSG have tags; subnets and associations do not support tags
- datalake: Storage Account has tags; containers do not support tags
- databricks: Workspace has tags
- monitoring: Monitor Workspace, Log Analytics, App Insights have tags
- keyvault: Key Vault, Managed Identity have tags; role assignments do not
- security: all resources are role assignments (no tags)
- ai: Cognitive Account has tags; deployment does not
- aks: Cluster and Node Pool have tags; role assignments do not

**Conclusion:** tagging is consistent with the provider's capabilities.

---

## Validation

### Cost analysis

| Item | Value |
|------|-------|
| Estimated total cost | ~$0.25 |
| Estimated monthly cost (destroy cycles) | < $0.03 |
| Orphaned resources removed | 2 (Storage Account, Access Connector) |
| Orphaned cost eliminated | < $0.01/month |

### ADRs

| Item | Value |
|------|-------|
| Total ADRs | 10 |
| Retroactive ADRs created | 4 (007, 008, 009, 010) |
| ADRs by theme | 3 groups |

### Documentation

| Document | Purpose |
|----------|---------|
| `docs/executive-summary.md` | 5-minute overview |
| `docs/roadmap-journey.md` | Story of the project |
| `docs/operations/cost-analysis.md` | Cost posture |
| `docs/operations/README.md` (updated) | FinOps section |
| `docs/architecture/README.md` (updated) | Complete ADR index |

### Local checks

| Check | Result |
|-------|--------|
| Tagging consistency | Verified across 8 modules |
| Orphaned resources removed | Yes |
| Documentation complete | Yes |

---

## Lessons Learned

### What worked well

- **Retroactive ADRs are valuable.** Recording ADR-007 through ADR-010
  completed the decision log. Recording late is better than not recording.
- **The cost analysis forced honesty.** Admitting that the CLI does not
  expose billing data is more professional than pretending it does.
- **The executive summary and roadmap journey are powerful.** They make
  the project accessible to readers who do not have time to read every
  phase document.

### Adjustments made

1. **Orphaned resource detection.** The Managed Resource Group was not
   destroyed by Terraform. This was discovered in Phase 10 when auditing
   resource groups. The procedure to detect and remove it was added to
   the operations checklist.

2. **Billing API limitation.** The Azure for Students subscription does
   not expose billing data via the CLI. The cost analysis uses estimates
   and clearly states this limitation.

3. **ADR consolidation.** The ADR index was updated to reflect all 10
   ADRs, with a thematic navigation for easier reading.

### What would be done differently

- **Verify orphaned resources after each destroy.** This should have
  been part of the operations checklist from Phase 1.
- **Create ADRs when decisions are made.** Waiting until Phase 10 to
  record ADR-007 through ADR-010 was a symptom of the early phases
  being focused on execution over documentation.

---

## Artifacts

### Documentation

| Artifact | Path | Purpose |
|----------|------|---------|
| Cost Analysis | `docs/operations/cost-analysis.md` | Cost posture and FinOps practices |
| Executive Summary | `docs/executive-summary.md` | 5-minute overview |
| Roadmap Journey | `docs/roadmap-journey.md` | Story of the project |
| Phase 10 | `docs/phases/phase-10-governance.md` | This document |
| ADR-007 | `docs/architecture/adr-007-azure-for-students.md` | Subscription decision |
| ADR-008 | `docs/architecture/adr-008-three-environments.md` | Environment structure |
| ADR-009 | `docs/architecture/adr-009-terraform.md` | IaC tool decision |
| ADR-010 | `docs/architecture/adr-010-network-topology.md` | Network topology |

### Updates

| Document | Change |
|----------|--------|
| `docs/operations/README.md` | Added "FinOps Practices" section |
| `docs/architecture/README.md` | Added ADRs 005-010, "Retroactive ADRs" section, "ADRs by Theme" section |
| `docs/README.md` | Added "Overview Documents" section |
| `README.md` | Updated project status to "Completed" |

---

## Project Closure

This phase marks the official conclusion of the project roadmap.

### What Was Delivered

- 10 phases, each with a documented record
- 10 ADRs, each with context, decision, and alternatives
- 8 Terraform modules, all validated
- 15 tests passing
- A tested DR strategy with 4 runbooks
- A local Kubernetes demonstration with monitoring
- A functional data pipeline with real data
- A comprehensive security model
- An executive summary and a roadmap journey

### What Was Not Delivered (and Why)

- **Databricks cluster** — SKU not available in the for Students subscription (ADR-001)
- **Azure OpenAI** — quota not available in the for Students subscription (ADR-004)
- **AKS cluster** — cost of the Load Balancer exceeds the credit (ADR-005)
- **CI/CD execution** — billing not available in the for Students subscription (Phase 4)

All of these are documented as out-of-scope limitations with activation
procedures for when the subscription upgrades.

### What the Project Demonstrates

- Technical competence across Azure, Terraform, Python, Kubernetes, and observability
- Ability to adapt to constraints without compromising the intent
- Discipline in documentation, testing, and decision records
- Honesty about what was and was not delivered

These qualities are appropriate for a portfolio project of this scope.

---

## Next Steps

There is no Phase 11. The roadmap is complete.

For future work, see the "Improvements pending subscription upgrade"
section in the main README. Those improvements are planned but not
scheduled.

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Phase 10 completed; roadmap officially closed |