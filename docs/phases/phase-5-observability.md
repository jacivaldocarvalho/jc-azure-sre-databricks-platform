# Phase 5 — Observability

**Status:** Completed
**Duration:** Multi-iteration (SLO definition, infrastructure provisioning, instrumentation, dashboards, alerts)
**Dependencies:** Phase 4 (CI/CD)

---

## Objective

Establish observability for the data pipeline by:

- Defining Service Level Indicators (SLIs) and Service Level Objectives (SLOs) *before* choosing any tool
- Provisioning the Azure infrastructure required to receive and store custom metrics
- Instrumenting the Python pipeline to emit metrics on every execution
- Creating dashboards and alerts that reflect the SLOs

The result is not just a collection of graphs, but a coherent observability model where every alert has a purpose and every metric serves an SLO.

---

## Context

### Why observability matters

A data pipeline that runs without metrics is a pipeline that fails silently. Without observation, the operator only learns about a problem when a downstream consumer complains — which is too late. Observability converts "we hope it works" into "we know it works, and we know when it doesn't."

### Why SLOs come first

The common mistake in portfolio projects is to start with a tool (Grafana, Prometheus) and then ask "what can we measure?". The professional approach is the reverse:

1. Define what reliability means for this service
2. Choose indicators that capture that reliability
3. Set measurable objectives
4. Then pick the tools that support those objectives

This phase follows that order.

### The service under observation

The "service" is the data pipeline that:

- Fetches Brazilian economic series (Selic, CDI, IPCA) from the BCB SGS API
- Validates the data against a declarative schema
- Transforms and aggregates the data
- Persists the results in Delta Lake format

The pipeline is currently executed locally. When a Databricks cluster becomes available, the same code runs on the workspace without modification.

---

## Architectural Decisions

### Decision 1: Azure Monitor managed Prometheus + Grafana in Azure Monitor

Three options were considered for the observability stack:

| Option | Description | Trade-off |
|--------|-------------|-----------|
| **A** | Azure Monitor managed Prometheus + Grafana in Azure Monitor | Free visualization, managed Prometheus, no server to maintain |
| **B** | Azure Monitor managed Prometheus + Azure Managed Grafana | Full Grafana features, but ~$72/month after a 30-day trial |
| **C** | Self-hosted Prometheus and Grafana on AKS | Full control, but requires AKS (not yet provisioned) and operational overhead |

**Decision:** Option A initially, adjusted during implementation to **Application Insights as the metrics backend** (see Decision 3).

### Decision 2: SLIs and SLOs defined before implementation

The SLIs and SLOs were documented in `monitoring/slos.md` *before* any infrastructure was provisioned. This ensured the tooling served the objectives and not the other way around.

The defined SLOs are:

| SLI | SLO | Window |
|-----|-----|--------|
| Pipeline availability | 99% | 30 days |
| Execution latency (P95) | < 120s | 7 days |
| Validation error rate | < 1% | 30 days |
| Data freshness | < 24h | Continuous |
| Processed volume | > 1000 records | Per run |

The error budget policy (what to do when the budget is depleted) is also documented.

### Decision 3: Application Insights as the metrics backend

During implementation, a key distinction became clear: the **Azure Monitor Workspace** (managed Prometheus) and the **Application Insights** (custom metrics via OpenTelemetry SDK) are different backends with different purposes.

| Backend | What it stores | How it is queried | When to use |
|---------|----------------|-------------------|-------------|
| Azure Monitor Workspace | Prometheus metrics | PromQL | Infrastructure metrics, Kubernetes workloads |
| Application Insights | Custom metrics, logs, traces | KQL, Azure Monitor Metrics | Application-level metrics from SDKs |

The `azure-monitor-opentelemetry-exporter` package (the official Microsoft SDK) sends metrics to Application Insights, not to the managed Prometheus endpoint. Migrating to send directly to the Prometheus endpoint would require a different approach (OTLP collector with authentication), adding significant complexity without proportional value for this project.

**Decision:** Use **Application Insights** as the metrics backend. The Azure Monitor Workspace remains provisioned as an architectural artifact but is not the backend for the pipeline's custom metrics. This is documented and intentional.

**Trade-off accepted:**
- **Gained:** Simplicity, working metrics from day one, native integration with Azure Monitor alerts
- **Lost:** PromQL queries for pipeline metrics; dashboards must use KQL or Azure Monitor Metrics

**Mitigation:** The Grafana in Azure Monitor remains available for future infrastructure metrics, and the Application Insights can be added as a data source to Grafana if needed.

---

## Implementation

### 1. Observability infrastructure (Terraform)

Added to `terraform/modules/monitoring/`:

- `azurerm_monitor_workspace` — Azure Monitor Workspace (managed Prometheus)
- `azurerm_log_analytics_workspace` — backend for Application Insights
- `azurerm_application_insights` — receives custom metrics from the pipeline

Outputs exposed:

- `workspace_id`, `workspace_name`, `query_endpoint`
- `application_insights_connection_string` (sensitive)

### 2. Metrics module (`python/src/utils/metrics.py`)

Provides:

- `setup_metrics()` — initializes the OpenTelemetry MeterProvider with the Azure Monitor exporter
- `shutdown_metrics()` — flushes pending metrics before process exit
- `track_duration()` — context manager to record stage durations
- Resource attributes: `service.name`, `service.namespace`, `service.version`, `deployment.environment`

The exporter is only configured when `APPLICATIONINSIGHTS_CONNECTION_STRING` is set. If not set, metrics are recorded but not exported — allowing development without observability infrastructure.

### 3. Pipeline metrics instruments (`python/src/utils/pipeline_metrics.py`)

Defines a `PipelineMetrics` dataclass with all instruments:

| Instrument | Type | Description |
|------------|------|-------------|
| `pipeline_runs_total` | Counter | Runs by status (success, failure) |
| `pipeline_rows_processed_total` | Counter | Rows processed by series and stage |
| `pipeline_rows_rejected_total` | Counter | Rows rejected during validation |
| `pipeline_api_requests_total` | Counter | BCB API requests by series and status |
| `pipeline_duration_seconds` | Histogram | Duration by stage |
| `pipeline_api_request_duration_seconds` | Histogram | BCB API latency by series |
| `pipeline_last_success_timestamp` | UpDownCounter | Unix timestamp of last successful run |

The instruments are created lazily via `initialize()`, which must be called after `setup_metrics()`. This avoids the Python import-order issue where module-level variables are copied by value instead of reference.

### 4. Instrumentation

**BCB API client** (`src/api/bcb_sgs.py`):
- Times each HTTP request to the SGS API
- Records success/failure status
- Records latency per series

**Ingestion** (`src/pipeline/ingest.py`):
- Records the row count per series after each ingestion

**Validation** (`src/pipeline/validate.py`):
- Records rejected rows when duplicates are found

**Orchestrator** (`src/run_pipeline.py`):
- Initializes metrics at startup
- Wraps each stage with `track_duration`
- Records success/failure of the overall run
- Records the last success timestamp on completion
- Shuts down metrics cleanly to ensure all data is flushed

### 5. Workbook (`Pipeline Overview`)

Created manually in Application Insights. Contains six panels:

1. **Executions by status** — bar chart of `pipeline_runs_total` grouped by status
2. **Stage durations (P50, P95, P99)** — time chart of `pipeline_duration_seconds`
3. **Volume by series** — bar chart of `pipeline_rows_processed_total`
4. **Freshness** — stat showing hours since last successful run
5. **BCB API latency (P95)** — time chart of `pipeline_api_request_duration_seconds`

### 6. Alert rules

Four alert rules were created in Azure Monitor, aligned with the SLOs:

| Alert | Severity | Trigger |
|-------|----------|---------|
| `pipeline-failure` | 1 (Error) | A run failed in the last 5 minutes |
| `pipeline-data-stale` | 1 (Error) | No successful run in over 24 hours |
| `pipeline-low-volume` | 2 (Warning) | Processed volume below 1000 rows per hour |
| `pipeline-slow` | 2 (Warning) | P95 duration above 120 seconds |

All rules send notifications to the `sre-oncall` action group (email).

---

## Validation

### Metrics confirmed in Application Insights

After running the pipeline, all seven metrics appeared in the Application Insights under the `azure.applicationinsights` namespace. The following were verified in the portal:

- `pipeline_runs_total` with `status="success"` label
- `pipeline_rows_processed_total` with three series: `selic` (505 rows), `cdi` (505 rows), `ipca` (24 rows)
- `pipeline_duration_seconds` with P50, P95, P99 all at ~42 seconds for the total stage
- `pipeline_last_success_timestamp` showing ~1.68 hours since the last run at the time of inspection
- `pipeline_api_request_duration_seconds` with P95 latency values: `cdi` (0.8s), `ipca` (0.5s), `selic` (0.49s)

### Workbook confirmed

All five panels of the `Pipeline Overview` workbook rendered correctly with data.

### Alerts confirmed

All four alert rules show status **Enabled** and are attached to the correct scope (`dev-sredatabricks-ai`).

### Commands used for local validation

```bash
# Run the pipeline
cd python
source .venv/bin/activate
python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31

# Confirm the export happened (search logs for)
# "Azure Monitor metrics exporter configured."
# "Metrics provider shut down cleanly."
```

---

## Lessons Learned

### What worked well

- **SLOs first:** defining SLIs/SLOs before any tool prevented the "collect everything" anti-pattern. Every metric serves a purpose.
- **OpenTelemetry SDK:** the standard SDK made instrumentation straightforward and vendor-neutral. Switching backends in the future would only require changing the exporter.
- **Separate modules for metrics:** `metrics.py` (infrastructure) vs `pipeline_metrics.py` (instruments) keeps concerns separated and makes testing easier.
- **Lazy instrument initialization:** avoiding module-level instrument creation sidestepped the Python import-order pitfall that caused the first failure.

### Adjustments made

1. **Python import-order bug:** the first version imported instruments directly (`from pipeline_metrics import api_requests_total`), which copied `None` into each module's namespace. Fixed by returning a `PipelineMetrics` object from `initialize()` and accessing instruments via the object.

2. **Pandera validation lazy mode:** earlier in the project, Pandera did not raise on schema violations because it defaults to lazy mode. Fixed with `lazy=False`.

3. **Application Insights workspace requirement:** the initial configuration tried to associate the Application Insights with the Azure Monitor Workspace, but the `workspace_id` attribute expects a **Log Analytics Workspace**, not an Azure Monitor Workspace. Fixed by adding a separate `azurerm_log_analytics_workspace`.

4. **KQL type mismatch in workbook and alerts:** `datetime_add()` requires a `long` argument, but `valueMax` is a `real`. Fixed with `tolong()` before passing to `datetime_add`.

5. **Metrics backend reassessment:** initial plan was to use managed Prometheus, but the `AzureMonitorMetricExporter` sends to Application Insights. This was documented as an intentional deviation rather than a bug.

### What would be done differently

- **Verify metrics backend early:** a small "hello world" test with the OpenTelemetry exporter against the intended backend would have surfaced the Application Insights vs Prometheus distinction before writing all the instrumentation.
- **Migrate workbook and alerts to Terraform from the start:** they were created manually to iterate faster, but this creates a manual step after each `terraform apply`. Documented in the post-apply checklist and planned for migration in a later phase.

---

## Artifacts

### Code

| Artifact | Path | Purpose |
|----------|------|---------|
| Metrics infrastructure | `python/src/utils/metrics.py` | OTel setup and export |
| Pipeline instruments | `python/src/utils/pipeline_metrics.py` | Metric definitions |
| Instrumented BCB client | `python/src/api/bcb_sgs.py` | API latency and requests |
| Instrumented ingestion | `python/src/pipeline/ingest.py` | Row counters |
| Instrumented validation | `python/src/pipeline/validate.py` | Rejection counters |
| Instrumented orchestrator | `python/src/run_pipeline.py` | Run lifecycle metrics |
| SLO document | `monitoring/slos.md` | SLIs, SLOs, error budgets |

### Azure resources (Terraform-managed)

| Resource | Name | Notes |
|----------|------|-------|
| Azure Monitor Workspace | `dev-sredatabricks-amw` | Prometheus backend (kept, not used for pipeline metrics) |
| Log Analytics Workspace | `dev-sredatabricks-law` | Backend for Application Insights |
| Application Insights | `dev-sredatabricks-ai` | Metrics backend for the pipeline |

### Azure resources (created manually)

| Resource | Name | Notes |
|----------|------|-------|
| Workbook | `Pipeline Overview` | 5 panels for the SLIs |
| Action Group | `sre-oncall` | Email notification target |
| Alert rules | `pipeline-failure`, `pipeline-data-stale`, `pipeline-low-volume`, `pipeline-slow` | Aligned with SLOs |

**Post-apply note:** the manual resources are documented in `docs/operations/README.md`. They must be recreated after each `terraform destroy` + `terraform apply` cycle until migration to Terraform is completed (planned for a later phase).

---

## Next Phase

[Phase 6 — Security](../phases/phase-6-security.md): implement RBAC, Managed Identities, and Key Vault integration.

