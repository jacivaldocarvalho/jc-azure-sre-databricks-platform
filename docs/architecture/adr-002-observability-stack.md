# ADR-002 — Observability Stack Selection

**Status:** Accepted
**Date:** 2026-09-24
**Deciders:** Project author
**Context:** Phase 5 (Observability)

---

## Context and Problem Statement

Phase 5 required the project to have observability over the data pipeline. Three questions needed answers before any code or infrastructure was written:

1. **What** should be observed? (Which signals matter?)
2. **Where** should the signals be stored? (Which backend?)
3. **How** should they be visualized and alerted on? (Which tooling?)

This ADR captures the reasoning behind each decision.

---

## Decision 1 — Define SLIs and SLOs before choosing tools

### Problem

The common approach in side projects is to start with a tool (Grafana, Prometheus, Datadog) and then look for things to measure. This leads to dashboards full of metrics no one acts upon.

### Options

| Option | Description |
|--------|-------------|
| A | Choose the tool first, then figure out what to measure |
| B | Define SLIs/SLOs first, then select tools that support them |

### Decision

**Option B.**

The document `monitoring/slos.md` was written before any infrastructure was provisioned. It defines:

- Five SLIs: availability, latency, error rate, freshness, volume
- Five SLOs: 99% availability, P95 latency < 120s, error rate < 1%, freshness < 24h, volume > 1000 rows
- An error budget policy that dictates operational behavior when the budget is depleted

### Consequences

**Positive:**
- Every metric has a purpose tied to an SLO
- Alerts are actionable, not noise
- The observability model survives tool replacement

**Negative:**
- Slower start — no immediate "wow" dashboard
- Requires discipline to define SLOs before having data

### References

- Google SRE Book — Service Level Objectives
- Google SRE Workbook — Implementing SLOs

---

## Decision 2 — Observability stack composition

### Problem

Which stack to adopt for collecting, storing, visualizing, and alerting on the pipeline's metrics?

### Options

| Option | Storage | Visualization | Cost | Notes |
|--------|---------|---------------|------|-------|
| A | Azure Monitor managed Prometheus | Grafana in Azure Monitor | Free | Managed, no server to maintain |
| B | Azure Monitor managed Prometheus | Azure Managed Grafana | ~$72/month after trial | Full Grafana features, but 72% of the total Azure for Students credit consumed in one month |
| C | Self-hosted Prometheus | Self-hosted Grafana on AKS | Free (excluding AKS) | Full control, but requires AKS and operational overhead |
| D | Application Insights | Azure Monitor Workbook | Free (pay per ingestion only) | Native integration, KQL queries, no server |
| E | Application Insights | Azure Monitor Workbook + Grafana | Free | D with optional Grafana integration |

### Decision

**Option E** — Application Insights as the metrics backend, with the Workbook for visualization and optional Grafana integration via the Azure Monitor data source.

This was an **adjustment** from the initially planned Option A. See Decision 3 for the reasoning.

### Consequences

**Positive:**
- No instance cost — the Application Insights and Workbook are free at the project's ingestion volume
- Native integration with Azure Monitor alerts (no additional alerting service)
- KQL is expressive and powerful for custom metrics
- Metrics from the OpenTelemetry SDK are first-class citizens

**Negative:**
- PromQL is not available for pipeline metrics — dashboards use KQL or Azure Monitor Metrics
- Grafana cannot natively query Application Insights without the Azure Monitor data source
- The Azure Monitor Workspace (managed Prometheus) remains provisioned but underused

**Mitigations:**
- The Azure Monitor Workspace stays available for future infrastructure metrics (e.g., AKS in Phase 8)
- The Workbook is sufficient for the current SLIs
- Grafana can be added later as a client of the Application Insights data source

### References

- Azure Monitor Workspace documentation
- Application Insights custom metrics documentation
- OpenTelemetry Azure Monitor exporter documentation

---

## Decision 3 — Adjust the plan: Application Insights instead of managed Prometheus for pipeline metrics

### Problem

The original plan (Documented in the Phase 5 objective) was to send pipeline metrics to the **Azure Monitor Workspace** (managed Prometheus) and visualize them in **Grafana in Azure Monitor** using **PromQL**.

During implementation, a technical constraint emerged: the official Microsoft SDK for Python (`azure-monitor-opentelemetry-exporter`) sends metrics to **Application Insights**, not to the managed Prometheus endpoint. The two are distinct backends.

### Investigation

| Approach | Complexity | Fit |
|----------|-----------|-----|
| Use `AzureMonitorMetricExporter` (default) → sends to Application Insights | Low | Application-level metrics, KQL queries |
| Configure OTLP exporter with direct authentication to managed Prometheus endpoint | High | Requires OTLP collector or custom auth, more setup |
| Use Prometheus Pushgateway → scrape to managed Prometheus | Medium | Works for batch jobs, but adds a component |

The Application Insights path was already validated: all seven pipeline metrics appeared correctly in the portal.

### Decision

**Keep the Application Insights as the metrics backend.** Document the adjustment as intentional.

### Rationale

1. **Working from day one:** metrics are being collected and visualized correctly without additional components
2. **Aligned with Microsoft guidance:** the official SDK targets Application Insights, and Microsoft recommends it as the default for application metrics
3. **No cost penalty:** Application Insights ingestion cost is minimal at the project's volume
4. **No loss of capability for the SLOs:** the defined SLIs (availability, latency, freshness, volume) are all measurable in Application Insights
5. **Migration path preserved:** if a future phase needs PromQL or managed Prometheus, an OTLP exporter can be added without changing the instrumentation

### Consequences

**Positive:**
- Implementation completed without rewriting the instrumentation layer
- Documentation reflects reality

**Negative:**
- The originally stated "PromQL dashboards" objective was not met literally
- PromQL-based alerting patterns are not applicable

**Mitigation:**
- Alerting uses Azure Monitor alert rules (KQL-based), which are equivalent in function
- The distinction is documented so future contributors understand the choice

### Alternatives Considered

- **Revert to managed Prometheus with OTLP:** rejected because it adds significant complexity (collector, authentication, pipeline rewrite) without proportional value for the project's scope
- **Dual-export (Application Insights + Prometheus):** rejected because it duplicates infrastructure and increases maintenance for no clear benefit

---

## Decision 4 — Workbook and alert rules created manually (for now)

### Problem

The Workbook (`Pipeline Overview`) and the four alert rules (`pipeline-failure`, `pipeline-data-stale`, `pipeline-low-volume`, `pipeline-slow`) were created in the Azure portal, not via Terraform.

### Options

| Option | Description |
|--------|-------------|
| A | Everything via Terraform, from the start |
| B | Manual creation now, migration to Terraform in a later phase |

### Decision

**Option B.**

### Rationale

1. **Iteration speed:** creating and adjusting workbook panels in the portal is significantly faster than editing and applying Terraform
2. **Learning curve:** the KQL queries required correction (`tolong()` for `datetime_add`), which would have required multiple Terraform apply cycles if done as code from the start
3. **Time budget:** the phase was already long; keeping the manual step allowed the phase to close on schedule
4. **Explicit migration path:** the resources are documented and will be codified

### Consequences

**Positive:**
- Phase 5 closed faster and with functional dashboards and alerts
- The KQL queries were validated interactively, then preserved for later codification

**Negative:**
- After each `terraform destroy` + `apply`, the Workbook, Action Group, and Alert Rules must be recreated manually
- This creates friction for anyone reproducing the project

**Mitigations:**
- `docs/operations/README.md` includes a "Post-apply checklist" listing the manual resources to recreate
- Migration to Terraform is planned for a later phase
- The ADR is recorded so the reasoning is preserved

### Planned migration

The following resources will be codified in a future phase:

| Resource | Terraform Resource |
|----------|-------------------|
| Action Group | `azurerm_monitor_action_group` |
| Workbook | `azurerm_application_insights_workbook` |
| Alert Rules (4) | `azurerm_monitor_scheduled_query_rules_alert_v2` |

Target phase: **Phase 10** (Optimization and Governance) or earlier, if a phase requires it.

---

## References

- `monitoring/slos.md` — SLIs, SLOs, error budget policy
- `docs/phases/phase-5-observability.md` — full phase record
- OpenTelemetry Python SDK documentation
- Azure Monitor OpenTelemetry exporter documentation
- KQL reference for custom metrics

---

## Revision History

| Date | Change |
|------|--------|
| 2026-09-24 | Initial decision recorded |
