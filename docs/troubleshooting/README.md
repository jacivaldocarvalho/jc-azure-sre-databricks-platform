### Arquivo 2: `docs/troubleshooting/README.md`

# Troubleshooting

Guides for diagnosing and resolving common issues in the JC-Azure SRE Databricks Platform.

---

## Purpose

This directory collects the issues that have actually occurred during the project, together with their root cause and the solution applied. It is not a generic FAQ. Every entry here was encountered, investigated, and resolved.

The format is intentionally practical: symptom, diagnosis, root cause, resolution.

---

## Structure

```
docs/troubleshooting/
├── README.md               # This file
└── (future detailed guides will be added here)
```

---

## Known Issues and Solutions

### Terraform

#### Issue: `Module not installed`

**Symptom:**
```
Error: Module not installed
```

**Diagnosis:** a new module was added or removed, but Terraform was not reinitialized.

**Resolution:**
```bash
make terraform-init
```

Then re-run the plan.

---

#### Issue: `ResourceGroupNotFound` during apply

**Symptom:**
```
Error: creating Storage Account ... Resource group 'dev-sredatabricks-rg' could not be found.
```

**Diagnosis:** the Resource Group was destroyed outside Terraform (or by a previous `destroy`), but the local state still references it.

**Resolution:**
```bash
cd terraform/environments/dev
terraform state rm azurerm_resource_group.main
cd ../../..
make terraform-plan
make terraform-apply
```

---

#### Issue: `ConflictWithNetworkIntentPolicy` on NSG update

**Symptom:**
```
Error: updating Network Security Group ... ConflictWithNetworkIntentPolicy
```

**Diagnosis:** the NSG has a `DenyAllInbound` rule that conflicts with the Network Intent Policy injected by Databricks when VNet Injection is enabled.

**Resolution:** see ADR-001 and the Phase 2 documentation. The correct configuration is:

1. Adopt `NoAzureDatabricksRules` in the workspace
2. Enable Secure Cluster Connectivity (`no_public_ip = true`)
3. Pre-define the required Databricks NSG rules in Terraform
4. Retain `DenyAllInbound`

---

### Databricks

#### Issue: `SkuNotAvailable` when creating a cluster

**Symptom:**
```
Error: cannot create cluster: failed to reach RUNNING, got TERMINATED:
databricks_error_message: The VM size you are specifying is not available.
```

**Diagnosis:** the SKU is not available in the subscription/region. For Azure for Students, this is common: the total regional vCPU quota is 6 vCPUs and the supported SKU catalog is very restricted.

**Resolution:** this limitation is structural and cannot be resolved by configuration changes. See [ADR-001](../architecture/adr-001-databricks-cluster-limitation.md) for the full analysis. The project uses local execution for the pipeline.

---

#### Issue: `RequiredNsgRuleNotSupportedForPublicIPWorkspace`

**Symptom:**
```
Error: Creation of workspace with requiredNsgRule set to 'Disabled' is
only supported for workspaces with Secure Cluster Connectivity enabled
(enableNoPublicIp = true).
```

**Diagnosis:** `NoAzureDatabricksRules` requires SCC.

**Resolution:** set `no_public_ip = true` in `custom_parameters`. See Phase 2 documentation.

---

#### Issue: `dbfsAccountNameNotAvailable`

**Symptom:**
```
Error: Custom dbfs account name 'devsredata' is not available for use,
please select a different name and try again.
```

**Diagnosis:** the DBFS storage account name collides with the Data Lake storage account name. Storage account names are globally unique.

**Resolution:** the DBFS account name is derived by appending `dbw`:

```hcl
storage_account_name = "${var.storage_account_name}dbw"
```

---

### Python and PySpark

#### Issue: `ModuleNotFoundError: No module named 'distutils'`

**Symptom:** when running the pipeline, Python 3.12 fails to import `distutils`.

**Diagnosis:** Python 3.12 removed `distutils` from the standard library. PySpark 3.5.x still imports it through the Spark Connect path.

**Resolution:**

1. Install `setuptools>=64.0.0` (provides a compatibility shim)
2. Import `setuptools` before `pyspark` in the entry point

```python
import setuptools  # noqa: F401
import argparse
# ... rest
```

---

#### Issue: `ModuleNotFoundError: No module named 'pyarrow'` (or `grpc`)

**Symptom:** importing `pandera.pyspark` fails with missing `pyarrow` or `grpcio`.

**Diagnosis:** Pandera PySpark imports Spark Connect, which requires optional dependencies not installed by default.

**Resolution:** use the `connect` extra of PySpark and declare the transitive dependencies explicitly:

```txt
pyspark[connect]==3.5.3
pyarrow==17.0.0
grpcio>=1.48.1
grpcio-status>=1.48.1
googleapis-common-protos>=1.56.4
```

---

#### Issue: Pandera validation does not raise on invalid data

**Symptom:** `validate_raw` returns successfully even for invalid data, and the corresponding test fails with `DID NOT RAISE`.

**Diagnosis:** Pandera PySpark defaults to lazy validation. Errors are stored on the DataFrame, not raised.

**Resolution:** pass `lazy=False`:

```python
validated_df = RAW_SCHEMA.validate(df, lazy=False)
```

---

#### Issue: `AttributeError: 'SparkSession' object has no attribute 'create_dataframe'`

**Symptom:** tests fail when trying to create an empty DataFrame with a schema.

**Diagnosis:** the correct method name is `createDataFrame` (camelCase), not `create_dataframe`.

**Resolution:**

```python
spark.createDataFrame([], schema="col1 string, col2 int")
```

---

### Network and Connectivity

#### Issue: API requests to BCB SGS fail intermittently

**Symptom:** `requests.exceptions.ConnectionError` or `HTTPError` when running the pipeline.

**Diagnosis:** transient network issues, rate limiting, or the BCB endpoint being temporarily unavailable.

**Resolution:** wait a few minutes and retry. The pipeline is idempotent: it overwrites existing data.

---

## Contributing a Troubleshooting Entry

When you encounter a new issue, add an entry with:

1. **Symptom** — the exact error message or behavior
2. **Diagnosis** — how you investigated
3. **Root Cause** — the underlying reason
4. **Resolution** — the fix applied, with commands if relevant

Keep entries short and practical. Link to a phase document or ADR when the issue is architectural.

---

## Related Documentation

- [Phases](../phases/) — the context in which issues occurred
- [Architecture](../architecture/) — decisions behind the configuration
- [Operations](../operations/) — routine procedures
- [Conventions](../conventions.md) — project standards
