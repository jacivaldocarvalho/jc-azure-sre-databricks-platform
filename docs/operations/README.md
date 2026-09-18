# Operations

Runbooks, procedures, and operational guidance for the JC-Azure SRE Databricks Platform.

---

## Purpose

This directory holds the operational knowledge required to run, maintain, and recover the platform. The intent is to reduce the dependency on tribal knowledge: any qualified operator should be able to perform the documented tasks without needing the original author.

This is a working document. As new operational scenarios are encountered, they are documented here.

---

## Structure

```
docs/operations/
├── README.md               # This file
└── (future runbooks will be added here)
```

Planned runbooks, to be added as the project progresses:

| Runbook | Target Phase | Description |
|---------|--------------|-------------|
| `destroy-and-recreate.md` | Current | Destroy and recreate the environment from scratch |
| `rotate-credentials.md` | Phase 4 | Rotate Service Principal and Databricks tokens |
| `backup-and-restore.md` | Phase 9 | Back up and restore critical data |
| `incident-response.md` | Phase 5 | Response procedure for common incidents |
| `cost-review.md` | Phase 10 | Monthly cost review procedure |

---

## Day-to-Day Operations

### 1. Provision the Full Environment

```bash
cd ~/projetos/jc-azure-sre-databricks-platform
make terraform-init
make terraform-plan
make terraform-apply
```

Takes approximately 15 to 25 minutes, dominated by the Databricks Workspace creation.

### 2. Destroy the Environment

```bash
make terraform-destroy
```

Takes approximately 5 to 10 minutes.

**Note:** the Terraform state backend (`tfstate-rg` resource group and `tfstatejcsredatabricks` storage account) is **not** destroyed, as it is not managed by this Terraform configuration. To remove it, do so manually.

### 3. Run the Data Pipeline Locally

```bash
cd python
source .venv/bin/activate
python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
```

Takes 30 seconds to 2 minutes.

### 4. Run the Test Suite

```bash
cd python
source .venv/bin/activate
pytest tests/ -v
```

Takes approximately 15 to 25 seconds.

### 5. Clean Local Artifacts

```bash
cd python
rm -rf spark-warehouse .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

Removes Delta tables, Pytest cache, and Python bytecode.

---

## Routine Checks

### Weekly

- Review the Azure Portal for unexpected resources
- Check the subscription credit balance

### Before Each Session

- Confirm the correct subscription is active: `az account show`
- Confirm the `.env` file is present and populated

### After Each Session

- If resources were provisioned for the session, destroy them (`make terraform-destroy`)
- Verify the Terraform state is consistent: `terraform plan` should report no changes

---

## Escalation and Support

This is a solo portfolio project. There is no on-call rotation. The escalation path is:

1. Consult this documentation
2. Consult the phase documentation in `../phases/`
3. Consult the architecture ADRs in `../architecture/`
4. Consult the troubleshooting guides in `../troubleshooting/`
5. Consult the original cloud provider documentation (Microsoft, Databricks, Terraform)

---

## Related Documentation

- [Phases](../phases/) — what was implemented
- [Architecture](../architecture/) — architectural decisions
- [Troubleshooting](../troubleshooting/) — problem resolution guides
- [Conventions](../conventions.md) — project standards


