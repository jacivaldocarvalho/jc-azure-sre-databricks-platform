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
├── README.md                            # This file
├── disaster-recovery.md                 # RTO/RPO reference
├── dr-test-log.md                       # Record of executed DR tests
└── runbooks/
    ├── recover-terraform-state.md       # Rollback and undelete procedures
    ├── recover-keyvault-secret.md       # Secret recovery procedures
    ├── reprovision-environment.md       # Full rebuild procedure
    └── recover-from-lost-machine.md     # Machine recovery procedure
```

### Runbooks

| Runbook | Purpose |
|---------|---------|
| [recover-terraform-state.md](runbooks/recover-terraform-state.md) | Roll back the state to a previous version, undelete the state blob, undelete the state container |
| [recover-keyvault-secret.md](runbooks/recover-keyvault-secret.md) | Undelete a soft-deleted secret, re-provision the Key Vault, or recreate a lost secret |
| [reprovision-environment.md](runbooks/reprovision-environment.md) | Full rebuild of the Azure environment from Terraform |
| [recover-from-lost-machine.md](runbooks/recover-from-lost-machine.md) | Recover the developer environment after machine loss |

### Disaster Recovery documents

| Document | Purpose |
|----------|---------|
| [disaster-recovery.md](disaster-recovery.md) | Component inventory, criticality classification, RTO/RPO objectives, recovery strategies |
| [dr-test-log.md](dr-test-log.md) | Record of every DR test executed, with duration, result, and lessons learned |

### Planned runbooks

| Runbook | Target Phase | Description |
|---------|--------------|-------------|
| `rotate-credentials.md` | Phase 10 | Rotate Service Principal and Key Vault secrets |
| `incident-response.md` | Phase 10 | Response procedure for common incidents |
| `cost-review.md` | Phase 10 | Monthly cost review procedure |

---

## Day-to-Day Operations

### 1. Provision the Full Azure Environment

```bash
cd ~/projetos/jc-azure-sre-databricks-platform
make terraform-init
make terraform-plan
make terraform-apply
```

Takes approximately 15 to 25 minutes, dominated by the Databricks Workspace creation.

### 2. Destroy the Azure Environment

```bash
make terraform-destroy
```

Takes approximately 5 to 10 minutes.

**Note:** the Terraform state backend (`tfstate-rg` resource group and `tfstatejcsredatabricks` storage account) is **not** destroyed, as it is not managed by this Terraform configuration.

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

Takes approximately 25 to 30 seconds.

### 5. Clean Local Artifacts

```bash
cd python
rm -rf spark-warehouse .pytest_cache
find . -type d -name "__pycache__" -exec rm -rf {} +
```

Removes Delta tables, Pytest cache, and Python bytecode.

---

## Local Kubernetes (Kind)

The project supports running the API on a local Kubernetes cluster via Kind.
This is the primary way to demonstrate Kubernetes-related features without
provisioning AKS. See [ADR-005](../architecture/adr-005-aks-local-first.md).

### Full setup in four commands

```bash
make kind-up          # Create Kind cluster + NGINX Ingress (~2 min)
make kind-build       # Build the API image + load into Kind (~30 s with cache)
make kind-deploy      # Deploy the API via Helm (~1 min)
make kind-monitoring  # Install Prometheus + Grafana (~3-5 min)
```

After the setup completes:

- The API is accessible at `http://jc-sre.local`
- The Grafana dashboard is accessible via port-forward at `http://localhost:3000`
- Prometheus is accessible via port-forward at `http://localhost:9090`

### Prerequisites

| Tool | Version | Notes |
|------|---------|-------|
| Docker | 20.10+ | Required by Kind |
| Kind | 0.20+ | Kubernetes in Docker |
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.12+ | Chart packaging |

Also ensure `/etc/hosts` contains:

```
127.0.0.1  jc-sre.local
```

### Makefile targets

| Target | Purpose |
|--------|---------|
| `make kind-up` | Create the Kind cluster and install NGINX Ingress |
| `make kind-down` | Delete the Kind cluster |
| `make kind-build` | Build the API Docker image and load it into Kind |
| `make kind-deploy` | Deploy the API via Helm |
| `make kind-monitoring` | Install the kube-prometheus-stack |
| `make kind-monitoring-port-forward` | Forward Grafana and Prometheus ports |
| `make kind-status` | Show cluster, pods, and ingress status |
| `make kind-logs` | Tail the API logs |
| `make kind-all` | Full sequence: cluster + build + deploy |

### Accessing Grafana and Prometheus

The monitoring stack is exposed only within the cluster. Use port-forwards to access:

```bash
# Grafana
kubectl port-forward -n jc-sre svc/jc-sre-monitoring-grafana 3000:80

# Prometheus
kubectl port-forward -n jc-sre svc/jc-sre-monitoring-prometheus 9090:9090
```

| Service | URL | Credentials |
|---------|-----|-------------|
| Grafana | http://localhost:3000 | admin / prom-operator |
| Prometheus | http://localhost:9090 | (none) |

### Accessing the API

The API is exposed via Ingress at `http://jc-sre.local`. If the Ingress is not working, use port-forward directly:

```bash
kubectl port-forward -n jc-sre svc/jc-sre-api 8080:80
curl http://localhost:8080/health
```

### Verifying the monitoring pipeline

The monitoring pipeline has four stages. Verify each:

```bash
# 1. The API exposes metrics
kubectl exec -n jc-sre deploy/jc-sre-api -- curl -s http://localhost:8080/metrics | grep "^http_" | head

# 2. The ServiceMonitor is discovered
kubectl get servicemonitor -n jc-sre jc-sre-api

# 3. The Prometheus target is UP
kubectl port-forward -n jc-sre svc/jc-sre-monitoring-prometheus 9090:9090
# Open http://localhost:9090/targets and look for jc-sre-api

# 4. The dashboard renders
# Open http://localhost:3000 → Dashboards → JC SRE API - Overview
```

### Generating test traffic

The dashboard needs traffic to populate. Generate some with:

```bash
for i in {1..30}; do
  curl -s http://jc-sre.local/health > /dev/null
  curl -s http://jc-sre.local/series > /dev/null
  curl -s http://jc-sre.local/series/selic/latest > /dev/null
  curl -s http://jc-sre.local/summary > /dev/null
done
```

### Teardown

```bash
make kind-down
```

This removes the cluster and all workloads. The Docker image remains in
the local Docker daemon. To remove it:

```bash
docker rmi jc-sre-databricks-api:latest
```

---

## Disaster Recovery Quick Reference

The project has a defined disaster recovery posture. This section is a
quick reference for the most common scenarios. For the full procedures,
follow the links to the runbooks.

### Decision tree

```
              ┌─────────────────────────────────────┐
              │  What is the problem?               │
              └──────────────────┬──────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ State      │    │ Secret or  │    │ Machine    │
       │ corrupted  │    │ Key Vault  │    │ lost or    │
       │ or wrong   │    │ problem    │    │ unusable   │
       └─────┬──────┘    └─────┬──────┘    └─────┬──────┘
             │                 │                 │
             ▼                 ▼                 ▼
       ┌────────────┐    ┌────────────┐    ┌────────────┐
       │ recover-   │    │ recover-   │    │ recover-   │
       │ terraform- │    │ keyvault-  │    │ from-lost- │
       │ state.md   │    │ secret.md  │    │ machine.md │
       └────────────┘    └────────────┘    └────────────┘
```

### Common scenarios

| Scenario | Runbook | Estimated time |
|----------|---------|----------------|
| State file corrupted | [recover-terraform-state.md](runbooks/recover-terraform-state.md) (Procedure A) | 15 minutes |
| State file deleted | [recover-terraform-state.md](runbooks/recover-terraform-state.md) (Procedure B) | 5 minutes |
| State container deleted | [recover-terraform-state.md](runbooks/recover-terraform-state.md) (Procedure C) | 10 minutes |
| Secret deleted (soft) | [recover-keyvault-secret.md](runbooks/recover-keyvault-secret.md) (Procedure A) | 5 minutes |
| Secret missing after `terraform apply` | [recover-keyvault-secret.md](runbooks/recover-keyvault-secret.md) (Procedure B) | 3 minutes |
| Full environment rebuild | [reprovision-environment.md](runbooks/reprovision-environment.md) | 30-50 minutes |
| Lost developer machine | [recover-from-lost-machine.md](runbooks/recover-from-lost-machine.md) | 45 minutes - 2 hours |

### Backend protection

The Terraform state backend has the following protections enabled:

| Protection | Setting | Purpose |
|-----------|---------|---------|
| Blob versioning | Enabled | Roll back to any previous version |
| Blob soft delete | 30 days | Recover a deleted state blob |
| Container soft delete | 30 days | Recover a deleted container |

To verify or re-enable:

```bash
make protect-tfstate
```

To list the available versions:

```bash
make tfstate-versions
```

### RTO/RPO summary

| Component | RTO | RPO |
|-----------|-----|-----|
| Terraform state | 4 hours | 24 hours |
| Source code | 1 hour | 0 (Git push) |
| Application Insights secret | 2 hours | 7 days |
| Service Principal | 4 hours | N/A |
| Storage Account | 4 hours | 24 hours |
| Resource Group, VNet, NSG | 2 hours | 0 |
| Databricks Workspace | 4 hours | N/A |
| Data (Delta Lake) | 1 hour | 30 days |

The full list is in [disaster-recovery.md](disaster-recovery.md).

### Test log

Every DR test is recorded in [dr-test-log.md](dr-test-log.md). As of
2026-10-09, three tests have been executed:

| # | Scenario | Status | Duration |
|---|----------|--------|----------|
| 1 | Rollback of the Terraform state | Passed | ~15 minutes |
| 2 | Recovery of a Key Vault secret | Passed | ~3 minutes |
| 5 | Recovery from a lost machine | Partial | Not measured |

### Out of scope

The following scenarios are documented as out of scope for the current
subscription (Azure for Students):

- Multi-region failover
- Geo-redundant storage (GRS, RA-GRS)
- Automated backup of the Databricks Workspace
- Azure Site Recovery
- Backup of historical Application Insights metrics

See [disaster-recovery.md](disaster-recovery.md) for the reasoning.

---

## Post-Apply Checklist (Azure)

Some resources were created manually or are not fully managed by Terraform. They must be recreated or verified after each `terraform destroy` + `terraform apply` cycle.

### Why manual

For speed of iteration and KQL query tuning, the Workbook and alert rules were created in the portal first. The migration to Terraform is planned for a future phase. Additionally, the Azure DevOps Service Principal scope change was applied manually since the SP was created outside of Terraform.

The AI integration and AKS do not require manual recreation: their Terraform modules are preserved but commented out in the environment wiring (see [ADR-004](../architecture/adr-004-ai-integration.md) and [ADR-005](../architecture/adr-005-aks-local-first.md)).

### Resources to recreate or verify

After `make terraform-apply`, follow these steps:

#### 1. Application Insights Secret in Key Vault

After the new Application Insights is provisioned by Terraform, populate the Key Vault with the new connection string:

```bash
cd terraform/environments/dev

# Get the connection string
terraform output -raw application_insights_connection_string > /tmp/ai-conn.txt

# Ensure no trailing newline
tr -d '\n' < /tmp/ai-conn.txt > /tmp/ai-conn-clean.txt

# Store in Key Vault
az keyvault secret set \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" \
  --file /tmp/ai-conn-clean.txt

# Clean up temporary files
rm /tmp/ai-conn.txt /tmp/ai-conn-clean.txt
```

If the secret already exists (soft-deleted from previous destroy), purge it first:

```bash
az keyvault secret delete \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" 2>/dev/null || true

az keyvault secret purge \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" 2>/dev/null || true
```

#### 2. Action Group

| Field | Value |
|-------|-------|
| Name | `sre-oncall` |
| Display name | `SRE On-Call` |
| Resource Group | `dev-sredatabricks-rg` |
| Notification type | Email |
| Email | the operator's address |

Location: **Monitor** → **Alerts** → **Action groups** → **Create**.

#### 3. Workbook

| Field | Value |
|-------|-------|
| Name | `Pipeline Overview` |
| Target | Application Insights `dev-sredatabricks-ai` |
| Save to | Shared Reports |

The workbook has five panels. The KQL queries for each panel are documented in `docs/phases/phase-5-observability.md`.

**Note:** For the freshness panel, use `tolong(valueMax)` before passing to `datetime_add()` to avoid the type error.

#### 4. Alert Rules

Create four alert rules against Application Insights `dev-sredatabricks-ai`:

| Name | Severity | Query filter |
|------|----------|--------------|
| `pipeline-failure` | 1 (Error) | Failures in the last 5 minutes |
| `pipeline-data-stale` | 1 (Error) | Freshness > 24 hours |
| `pipeline-low-volume` | 2 (Warning) | Volume < 1000 rows per hour |
| `pipeline-slow` | 2 (Warning) | P95 duration > 120 seconds |

All rules reference the `sre-oncall` action group.

The full KQL queries for each rule are documented in `docs/phases/phase-5-observability.md`.

#### 5. Verify Service Principal Scope

After recreating the environment, verify that the Azure DevOps Service Principal still has Contributor at the Resource Group scope:

```bash
SP_OID=$(az ad sp list --display-name "jc-sre-databricks-pipeline" --query "[0].id" -o tsv)

az role assignment list \
  --assignee "$SP_OID" \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**Expected:** Contributor at the Resource Group scope.

If the assignment is missing, recreate it:

```bash
az role assignment create \
  --assignee "$SP_OID" \
  --role "Contributor" \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg"
```

#### 6. Verify Managed Identity Role Assignments

The Terraform `security` module recreates the role assignments automatically. Verify:

```bash
# Databricks Managed Identity on Storage
az role assignment list \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg/providers/Microsoft.Storage/storageAccounts/devsredata" \
  --query "[].{Principal:principalId, Role:roleDefinitionName}" \
  -o table
```

**Expected:** one assignment with `Storage Blob Data Contributor`.

```bash
# Databricks Managed Identity on Key Vault
az role assignment list \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg/providers/Microsoft.KeyVault/vaults/dev-sredatabricks-kv" \
  --query "[].{Principal:principalId, Role:roleDefinitionName}" \
  -o table
```

**Expected:** two assignments (Key Vault Administrator for the user, Key Vault Secrets User for the Managed Identity).

#### 7. Verify AI and AKS Configuration

Neither AI nor AKS require manual recreation. Verify that the `.env` and Terraform configuration reflect the intended mode:

```bash
grep "AZURE_OPENAI" .env
```

**Expected in the current environment:**

```
AZURE_OPENAI_ENABLED=false
```

The AKS module is commented out. Its activation procedure is documented in [ADR-005](../architecture/adr-005-aks-local-first.md).

---

## Troubleshooting Local Kubernetes

### Pod stuck in `ContainerCreating`

**Symptom:** pod shows `ContainerCreating` for more than a few minutes.

**Cause:** the `hostPath` volume is not mounted correctly. In Kind, `hostPath` refers to the node's filesystem, not the host.

**Diagnosis:**

```bash
kubectl describe pod -n jc-sre -l app.kubernetes.io/name=jc-sre-api
```

**Fix:** ensure the cluster was created with `extraMounts` pointing to
`python/spark-warehouse`. Recreate the cluster:

```bash
make kind-down
make kind-up
```

### `PermissionError: /home/spark-warehouse`

**Symptom:** the API logs show `PermissionError` when initializing Spark.

**Cause:** the Spark code was computing the warehouse directory from
`__file__` instead of respecting `DELTA_WAREHOUSE_PATH`.

**Fix:** ensure `python/src/utils/spark.py` respects the
`DELTA_WAREHOUSE_PATH` environment variable (this was fixed in Phase 8).

### ServiceMonitor not discovered by Prometheus

**Symptom:** the dashboard in Grafana shows "No data" for API metrics.

**Cause:** the selector in the ServiceMonitor does not match the labels on
the Service.

**Diagnosis:**

```bash
kubectl get servicemonitor -n jc-sre jc-sre-api -o jsonpath='{.spec.selector.matchLabels}{"\n"}'
kubectl get svc -n jc-sre jc-sre-api --show-labels
```

The `matchLabels` in the ServiceMonitor must be a subset of the Service's
labels. In this project, both use `app.kubernetes.io/name=jc-sre-api`.

**Fix:** update the ServiceMonitor selector, then apply the Helm upgrade.

### `helm upgrade` fails with `Chart.yaml file is missing`

**Symptom:** Helm cannot read the chart even though `Chart.yaml` exists.

**Cause:** an overly aggressive `.helmignore` in the chart directory can
prevent Helm from reading essential files.

**Fix:** remove or disable the `.helmignore`:

```bash
mv kubernetes/helm/jc-sre-monitoring/.helmignore \
   kubernetes/helm/jc-sre-monitoring/.helmignore.disabled
```

Then retry the upgrade.

### Docker build fails with `Package openjdk-17-jre-headless is not available`

**Symptom:** the Docker build fails on the runtime stage.

**Cause:** `python:3.12-slim` moved from Debian 12 (Bookworm) to Debian 13
(Trixie), which replaced OpenJDK 17 with 21.

**Fix:** either update the Dockerfile to use `openjdk-21-jre-headless`, or
pin the base image to `python:3.12-slim-bookworm`. The project uses the
second approach for reproducibility.

---

## Security Auditing

The following checks should be performed periodically to maintain the security posture. See `docs/architecture/security-model.md` for the full model.

### Quarterly Audit

#### 1. Review role assignments

```bash
az role assignment list \
  --all \
  --query "[].{Principal:principalName, Type:principalType, Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**What to check:**
- No unexpected Service Principals have access
- No role assignments at the subscription scope other than the Owner
- The Azure DevOps SP has Contributor only at the Resource Group

#### 2. Review secrets and credentials

```bash
az keyvault secret list \
  --vault-name dev-sredatabricks-kv \
  --query "[].{Name:name, Enabled:attributes.enabled, Expires:attributes.expires}" \
  -o table

az ad app credential list \
  --id f0fa3958-4d24-45d1-bdb4-e8af5f4d7147 \
  --query "[].{Name:displayName, EndDate:endDateTime}" \
  -o table
```

**What to check:**
- All secrets are actively used
- No secrets near expiration without a rotation plan
- No orphaned secrets

**Note:** the Azure DevOps App Registration uses OIDC, so it should have **no** client secrets. If any appear, investigate and revoke.

#### 3. Review the Managed Identity

```bash
az identity show \
  --name dev-sredatabricks-dbw-mi \
  --resource-group dev-sredatabricks-rg \
  --query "{Name:name, ClientId:clientId, PrincipalId:principalId}" \
  -o table

MI_PRINCIPAL=$(az identity show --name dev-sredatabricks-dbw-mi --resource-group dev-sredatabricks-rg --query principalId -o tsv)

az role assignment list \
  --assignee "$MI_PRINCIPAL" \
  --all \
  --query "[].{Role:roleDefinitionName, Scope:scope}" \
  -o table
```

**What to check:**
- Only the expected roles are present
- No unexpected scope expansion

#### 4. Review the Key Vault access

```bash
az role assignment list \
  --scope "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/dev-sredatabricks-rg/providers/Microsoft.KeyVault/vaults/dev-sredatabricks-kv" \
  --query "[].{Principal:principalName, Type:principalType, Role:roleDefinitionName}" \
  -o table
```

**What to check:**
- Only the operator and the Databricks Managed Identity have access
- No Service Principals have access unless explicitly required

### Rotation Procedures

#### Rotating the Application Insights connection string

```bash
cd terraform/environments/dev
terraform apply -replace=module.monitoring.azurerm_application_insights.main

terraform output -raw application_insights_connection_string > /tmp/ai-conn.txt
tr -d '\n' < /tmp/ai-conn.txt > /tmp/ai-conn-clean.txt

az keyvault secret set \
  --vault-name dev-sredatabricks-kv \
  --name "applicationinsights-connection-string" \
  --file /tmp/ai-conn-clean.txt

rm /tmp/ai-conn.txt /tmp/ai-conn-clean.txt
```

#### Rotating the Azure CLI session

```bash
az logout
az login
az account set --subscription <SUBSCRIPTION_ID>
```

#### Enabling Azure OpenAI (when quota becomes available)

See [ADR-004](../architecture/adr-004-ai-integration.md) for the step-by-step procedure.

#### Enabling the AKS cluster (when credit becomes available)

See [ADR-005](../architecture/adr-005-aks-local-first.md) for the step-by-step procedure.

#### Revoking the Azure DevOps Federated Credential

```bash
az ad app federated-credential list --id f0fa3958-4d24-45d1-bdb4-e8af5f4d7147 -o table

az ad app federated-credential delete \
  --id f0fa3958-4d24-45d1-bdb4-e8af5f4d7147 \
  --federated-credential-id <credential-name>
```

Recreate it with the exact issuer and subject that Azure DevOps generates.

---

## Routine Checks

### Weekly

- Review the Azure Portal for unexpected resources
- Check the subscription credit balance
- Review the `Pipeline Overview` workbook for anomalies
- Confirm no alerts are firing
- Verify the AI summary mode in the last pipeline log

### Before Each Session

- Confirm the correct subscription is active: `az account show`
- Confirm the `.env` file is present and populated
- Confirm `AZURE_USE_CLI=true` is set for local development

### After Each Session

- Destroy Azure resources if they were provisioned (`make terraform-destroy`)
- Tear down the Kind cluster if it was created (`make kind-down`)
- Verify the Terraform state is consistent: `terraform plan` should report no changes

---

## Escalation and Support

This is a solo portfolio project. There is no on-call rotation. The escalation path is:

1. Consult this documentation
2. Consult the phase documentation in `../phases/`
3. Consult the architecture ADRs in `../architecture/`
4. Consult the troubleshooting guides in `../troubleshooting/`
5. Consult the original cloud provider documentation (Microsoft, Databricks, Terraform, Kind, Helm)

---

## Related Documentation

- [Phases](../phases/) — what was implemented
- [Architecture](../architecture/) — architectural decisions
- [Security Model](../architecture/security-model.md) — full security posture
- [AI Integration Strategy](../architecture/adr-004-ai-integration.md) — AI decisions and activation procedure
- [AKS Local-First Strategy](../architecture/adr-005-aks-local-first.md) — Kubernetes decisions and activation procedure
- [Disaster Recovery Strategy](../architecture/adr-006-dr-strategy.md) — DR decisions and rationale
- [Disaster Recovery Reference](disaster-recovery.md) — RTO/RPO objectives and inventory
- [DR Test Log](dr-test-log.md) — record of executed tests
- [Troubleshooting](../troubleshooting/) — problem resolution guides
- [Conventions](../conventions.md) — project standards
