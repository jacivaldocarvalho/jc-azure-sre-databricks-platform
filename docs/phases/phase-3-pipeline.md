# Phase 3 — Data Pipeline

**Status:** Completed
**Duration:** Multi-iteration (environment setup, dependency resolution, validation tuning)
**Dependencies:** Phase 2 (Databricks Workspace and Data Lake)

---

## Objective

Implement a functional data pipeline that ingests real data from a public source, validates it against a declarative schema, transforms it into meaningful aggregates, and persists the results in Delta Lake format.

The pipeline is designed to run identically in two environments:

- **Local development** — PySpark + Delta Lake, no cloud dependency
- **Databricks** — same code, executed against the workspace provisioned in Phase 2

This duality demonstrates portability and separation of concerns between business logic and execution environment.

---

## Context

### Source of Data

Chosen source: **Banco Central do Brasil — SGS API** (Sistema Gerenciador de Séries Temporais).

| Series | SGS Code | Frequency | Unit |
|--------|----------|-----------|------|
| Selic | 11 | Daily | % per day |
| CDI | 12 | Daily | % per day |
| IPCA | 433 | Monthly | % per month |

The SGS API is:

- Public, no authentication required
- Stable and well-documented
- A source of authoritative Brazilian economic data
- Subject to a 10-year window limit per request (handled by chunking)

### Architectural Decision: Local Execution

The original plan was to run the pipeline directly in a Databricks cluster. However, the Azure for Students subscription has structural limitations that prevent cluster provisioning:

- Total regional vCPU quota: 6 vCPUs
- No compatible SKUs available in any of the five allowed regions (`eastus`, `northcentralus`, `centralus`, `brazilsouth`, `spaincentral`)
- The Databricks supported SKU list does not include the v6/v7 generations available in `brazilsouth`

**Decision:** Run the pipeline locally with the same code that would run on Databricks. Document the limitation in an ADR (`adr-001-databricks-cluster-limitation.md`).

### Layered Architecture

The pipeline follows a layered data architecture inspired by the medallion pattern:

| Layer | Purpose | Storage |
|-------|---------|---------|
| Raw | Ingestion output, unchanged | Delta partition by series |
| Processed | Transformed and aggregated | Delta tables per metric |

### Separation of Concerns

- **Business logic** lives in `python/src/pipeline/` — testable, reusable
- **Orchestration** lives in `python/src/run_pipeline.py` — thin, environment-aware
- **API clients** live in `python/src/api/` — swappable, isolated

---

## Implementation

### 1. API Client (`src/api/bcb_sgs.py`)

- Wraps the SGS API with a dataclass-based series registry
- Handles the 10-year window limit by chunking requests automatically
- Returns a normalized list of dictionaries

### 2. Ingestion (`src/pipeline/ingest.py`)

- Fetches each configured series
- Converts JSON to Spark DataFrame with the target schema
- Adds metadata columns: `series`, `unit`, `frequency`, `ingested_at`
- Unions all series into a single DataFrame

### 3. Validation (`src/pipeline/validate.py`)

- Uses Pandera PySpark for declarative schema validation
- Enforces column types, non-null constraints, and allowed values for `series` and `frequency`
- Additionally checks for duplicate `(series, date)` pairs
- Uses `lazy=False` to force immediate failure on schema violations
- Logs a summary: row count, distinct series, date range

### 4. Transformation (`src/pipeline/transform.py`)

- **Annualization:** converts daily rates to annualized rates using 252 business days (`((1 + daily/100)^252 - 1) * 100`)
- **Time dimensions:** adds `year`, `month`, `day`, `weekday`
- **Variations:** computes absolute and percentual day-over-day variation per series
- **Monthly aggregation:** computes mean, min, max, stddev, and observation count per series per month

### 5. Persistence (`src/pipeline/persist.py`)

- Generic `write_delta` function supporting overwrite and partitioning
- Raw layer partitioned by `series` for query isolation
- Processed layer organized as named tables (`variations`, `monthly_aggregates`)
- Compatible with local paths and ABFSS endpoints without code changes

### 6. Orchestration (`src/run_pipeline.py`)

Six-step flow:

1. Ingest all series
2. Validate against schema
3. Persist raw layer
4. Transform (annualization, time, variations)
5. Aggregate monthly
6. Persist processed layer

CLI arguments: `--start YYYY-MM-DD`, `--end YYYY-MM-DD`.

Defaults: last 12 months.

### 7. Local Environment

- Python 3.12 with `venv`
- PySpark 3.5.3 (with `connect` extra)
- Delta Lake 3.2.0
- Pandera 0.20.4 with Spark Connect dependencies
- Pytest 8.3.3 with coverage and mock plugins
- Ruff 0.7.1 for linting

Setup script `scripts/setup-local.sh` automates environment creation.

### 8. Test Suite

| Test file | Purpose | Count |
|-----------|---------|-------|
| `test_smoke.py` | Environment health (Spark, Delta, logger) | 3 |
| `test_transform.py` | Annualization, time dimensions, variations | 3 |
| `test_validate.py` | Schema pass/fail, empty DataFrame, tolerant mode | 4 |
| **Total** | | **10** |

All tests pass locally.

---

## Validation

### Run tests

```bash
cd python
source .venv/bin/activate
pytest tests/ -v
```

**Expected:** 10 tests pass.

### Run the pipeline

```bash
python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
```

**Expected output (abbreviated):**

```
Starting pipeline: 2024-01-01 to 2025-12-31
=== Step 1: Ingestion ===
Ingested series 'selic': 505 rows, 2024-01-02 to 2025-12-31
Ingested series 'cdi': 505 rows, 2024-01-02 to 2025-12-31
Ingested series 'ipca': 24 rows, 2024-01-01 to 2025-12-01
=== Step 2: Validation ===
Schema validation passed for 1034 rows.
=== Step 3: Persist raw ===
Wrote 1034 rows to ./spark-warehouse/raw
=== Step 4: Transformation ===
=== Step 5: Aggregation ===
=== Step 6: Persist processed ===
Wrote 1010 rows to ./spark-warehouse/processed/variations
Wrote 72 rows to ./spark-warehouse/processed/monthly_aggregates
Pipeline completed successfully.
```

### Inspect results

```bash
# Local Delta tables
ls -la spark-warehouse/raw/
ls -la spark-warehouse/processed/

# Query monthly aggregates
python -c "
from src.utils.spark import get_spark_session
spark = get_spark_session()
df = spark.read.format('delta').load('./spark-warehouse/processed/monthly_aggregates')
df.orderBy('series', 'year_month').show(20, truncate=False)
spark.stop()
"
```

**Data sanity check:** January 2024 CDI value of 0.0437% per day corresponds to approximately 10.9% per year, which is consistent with the actual Brazilian interest rate environment of the period.

---

## Lessons Learned

### What worked well

- Separating API client, ingestion, validation, transformation, and persistence into distinct modules made the code testable and readable
- Pandera schema as code catches structural issues early
- The chunking logic in the API client transparently handles the 10-year window limitation
- The same code path works locally and (in principle) on Databricks with no changes

### Adjustments made

1. **PySpark 3.5.3 + Python 3.12 compatibility** — the `distutils` module was removed from Python 3.12. PySpark 3.5.x still imports it via Spark Connect. Fixed by:
   - Adding `setuptools>=64.0.0` to dependencies
   - Importing `setuptools` before `pyspark` in the entry point

2. **Spark Connect optional dependencies** — Pandera's PySpark module imports Spark Connect, which requires `pyarrow`, `grpcio`, `grpcio-status`, and `googleapis-common-protos`. Fixed by switching to `pyspark[connect]` and declaring the transitive dependencies explicitly.

3. **Pandera lazy validation** — by default, Pandera PySpark does not raise exceptions on schema violations; it stores errors in the DataFrame. Fixed by calling `validate(df, lazy=False)`.

4. **Method name in tests** — `spark.create_dataframe` does not exist; the correct method is `spark.createDataFrame`. Fixed in test file.

5. **Local Spark session tuning** — the default shuffle partitions and heap settings were too aggressive for a laptop. Fixed by limiting `spark.sql.shuffle.partitions=4` and disabling the Spark UI.

### What would be done differently

- **Test data set up earlier:** running the pipeline for the first time exposed integration issues that could have been caught with a small mocked dataset.
- **Dependency audit before coding:** the distutils/grpcio/pyarrow chain was discovered iteratively. In a corporate environment, resolving these upfront via a lockfile would save time.

---

## Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| API client | `python/src/api/bcb_sgs.py` | SGS API wrapper |
| Ingestion | `python/src/pipeline/ingest.py` | Data fetching and DataFrame conversion |
| Validation | `python/src/pipeline/validate.py` | Pandera schema enforcement |
| Transformation | `python/src/pipeline/transform.py` | Annualization, variations, aggregation |
| Persistence | `python/src/pipeline/persist.py` | Delta Lake writes |
| Orchestration | `python/src/run_pipeline.py` | Main entry point |
| Utilities | `python/src/utils/` | Logging and Spark helpers |
| Tests | `python/tests/` | 10 unit and smoke tests |
| Requirements | `python/requirements.txt` | Pinned dependencies |
| Setup script | `scripts/setup-local.sh` | One-command environment setup |

**Local Delta tables produced:**

| Table | Path | Row count |
|-------|------|-----------|
| Raw | `spark-warehouse/raw/` | 1034 |
| Variations | `spark-warehouse/processed/variations/` | 1010 |
| Monthly aggregates | `spark-warehouse/processed/monthly_aggregates/` | 72 |

---

## Next Phase

[Phase 4 — CI/CD with Azure DevOps](../README.md): automate Terraform validation and notebook deployment via pipelines.
