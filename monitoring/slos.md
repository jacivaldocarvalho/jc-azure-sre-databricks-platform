# Service Level Objectives

Formal definition of the Service Level Indicators (SLIs) and Service Level Objectives (SLOs) for the JC-Azure SRE Databricks Platform data pipeline.

---

## Purpose

This document defines what "reliability" means for the data pipeline, how it is measured, and what targets are expected. It exists to answer three questions:

1. **What** do we measure?
2. **What** is the target?
3. **What** do we do when the target is not met?

Without these definitions, observability becomes a collection of graphs that no one acts upon. With them, alerts and dashboards have a clear purpose.

---

## The Service Under Observation

The service is the **data pipeline** that:

- Fetches Brazilian economic series (Selic, CDI, IPCA) from the BCB SGS API
- Validates the data against a declarative schema
- Transforms and aggregates the data
- Persists the results in Delta Lake format

The pipeline is currently executed locally. When a Databricks cluster becomes available, the same code runs on the workspace without modification.

---

## The Four Golden Signals

The SLIs are derived from the four golden signals of monitoring:

| Signal | Description | Applied to the Pipeline |
|--------|-------------|-------------------------|
| **Latency** | Time to respond | Total pipeline execution time |
| **Traffic** | Demand on the system | Number of executions and volume of data |
| **Errors** | Failed requests | Failures in ingestion, validation, or persistence |
| **Saturation** | Resource utilization | Memory, CPU, disk usage |

---

## Service Level Indicators (SLIs)

SLIs are the raw measurements. They describe what is being observed, not what is expected.

| SLI | Description | Formula | Unit |
|-----|-------------|---------|------|
| **Pipeline availability** | Successful runs over total runs | `successful_runs / total_runs` | % |
| **Execution latency** | Total pipeline execution time | P95 of `execution_duration_seconds` | seconds |
| **Validation error rate** | Rows rejected over total rows | `rejected_rows / total_rows` | % |
| **Data freshness** | Time since last successful run | `now() - last_success_timestamp` | hours |
| **Processed volume** | Records processed per run | `count(records)` | count |

### How each SLI is measured

**Pipeline availability**
Measured by comparing the exit status of the pipeline. A run is "successful" if it completes without raising an exception and persists all expected tables. A run is "failed" if any stage raises or if the expected output is missing.

**Execution latency**
Measured as the wall-clock time from the start of the first ingestion to the completion of the last write. The P95 is tracked over a rolling window of the last 30 runs.

**Validation error rate**
Measured by the ratio of rows that fail schema validation over the total rows ingested. In the current implementation, validation is strict (`lazy=False`), so any violation fails the run. This SLI is therefore 0% or 100% in practice, but the metric is still useful for tracking near-miss scenarios in future tolerant modes.

**Data freshness**
Measured as the time since the `ingested_at` timestamp of the most recent successful run. This is the primary signal that the pipeline is operating as expected.

**Processed volume**
Measured as the number of rows written to the `raw` table per run. Acts as a sanity check: a sudden drop to zero indicates a silent failure.

---

## Service Level Objectives (SLOs)

SLOs are the targets. They describe the expected behavior and define the error budget.

| SLI | SLO | Window | Rationale |
|-----|-----|--------|-----------|
| **Pipeline availability** | 99% | 30 days | Equivalent to ~7.2 hours of failure per month. Appropriate for a non-critical data pipeline. |
| **Execution latency (P95)** | < 120s | 7 days | Ingesting 2 years of data takes ~60s locally. 120s provides headroom for network variability and API rate limits. |
| **Validation error rate** | < 1% | 30 days | BCB data is authoritative. Failures indicate a real problem (schema change, API change, network issue) rather than data noise. |
| **Data freshness** | < 24h | Continuous | Data is expected to be refreshed daily. If it becomes stale for more than a day, something is wrong. |
| **Processed volume** | > 1000 records | Per run | Sanity threshold. A successful run should always process at least 1000 records given the data volume of the three series. |

---

## Error Budgets

The error budget is the complement of the SLO. If the SLO is 99%, the error budget is 1%.

| SLO | Error Budget (30 days) | Meaning |
|-----|------------------------|---------|
| 99% availability | 7.2 hours | The pipeline can fail for up to 7.2 hours in a 30-day window |
| 99.5% availability | 3.6 hours | The pipeline can fail for up to 3.6 hours |
| 99.9% availability | 43.2 minutes | The pipeline can fail for up to 43.2 minutes |

The project adopts **99% availability** as the target. This gives a comfortable error budget for a non-critical data pipeline while still imposing operational discipline.

### Error Budget Policy

| Error Budget Remaining | Action |
|------------------------|--------|
| **> 50%** | Normal operation. Continue regular development. |
| **25% - 50%** | Review logs. Investigate any degradation trend. |
| **10% - 25%** | Pause new changes. Focus on stability and root cause analysis. |
| **< 10%** | Incident mode. All work is on restoring the SLO. Postmortem required after resolution. |

This policy follows the Site Reliability Engineering practice of using error budgets to balance reliability and velocity. When the budget is healthy, the team can move fast. When the budget is depleted, the team slows down and prioritizes stability.

---

## Alerting Strategy

Alerts are derived from the SLOs. An alert fires when the SLO is at risk of being violated, not when it has already been violated.

| Alert | Trigger | Severity | Action |
|-------|---------|----------|--------|
| **Pipeline failure** | A run fails (exit code != 0) | Critical | Investigate immediately |
| **Pipeline slow** | P95 latency > 120s over 7 days | Warning | Investigate trend |
| **Data stale** | Last successful run > 24h ago | Critical | Investigate immediately |
| **Low volume** | Processed < 1000 records | Warning | Verify API availability |
| **Error budget low** | Availability < 99.5% over 30 days | Warning | Slow down, investigate |

### Alert principles applied

1. **Symptom-based, not cause-based.** Alerts describe what is wrong, not why. The investigation determines the cause.
2. **Actionable.** Every alert has a clear next step. Alerts that cannot be acted upon are removed.
3. **Tiered.** Critical alerts require immediate attention; warnings require review within a business day.
4. **SLO-linked.** Alerts fire before the SLO is violated, buying time to act.

---

## Metrics to Expose

The following metrics will be exposed by the pipeline and collected by the observability stack:

| Metric | Type | Description |
|--------|------|-------------|
| `pipeline_runs_total` | Counter | Total runs, labeled by status (success, failure) |
| `pipeline_duration_seconds` | Histogram | Execution duration, labeled by stage |
| `pipeline_rows_processed_total` | Counter | Rows processed, labeled by series and stage |
| `pipeline_rows_rejected_total` | Counter | Rows rejected during validation |
| `pipeline_last_success_timestamp` | Gauge | Unix timestamp of the last successful run |
| `pipeline_api_request_duration_seconds` | Histogram | BCB API request duration |
| `pipeline_api_requests_total` | Counter | BCB API requests, labeled by status |

These metrics form the foundation of the dashboards and alerts defined in Phase 5.

---

## What is Out of Scope

The following are intentionally not covered in this phase:

- **Infrastructure metrics** (VNet, Storage Account, Databricks workspace). These are managed services with their own monitoring. Infrastructure metrics will be added in Phase 8 when AKS is provisioned.
- **Business metrics** (e.g., "number of insights generated"). The pipeline does not yet produce business outcomes. This will be revisited in Phase 7 (AI integration).
- **Distributed tracing.** The pipeline is a single-process job. Tracing is not applicable.

---

## References

- [Google SRE Book — Service Level Objectives](https://sre.google/sre-book/service-level-objectives/)
- [Google SRE Workbook — Implementing SLOs](https://sre.google/workbook/implementing-slos/)
- [The Four Golden Signals](https://sre.google/sre-book/monitoring-distributed-systems/)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-09-24 | Initial SLIs, SLOs, and error budget policy defined |