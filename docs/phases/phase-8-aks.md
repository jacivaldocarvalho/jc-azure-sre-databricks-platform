# Phase 8 — AKS and Containerized Workloads

**Status:** Completed (with documented limitation)
**Duration:** Multi-iteration (module design, local fallback via Kind, API development, Helm packaging, observability stack)
**Dependencies:** Phase 7 (AI Integration)

---

## Objective

Deploy a containerized workload on Kubernetes, exposed via Ingress and
observed via Prometheus and Grafana. The phase was designed around Azure
Kubernetes Service (AKS), but the current subscription cannot afford it.
The decision was to preserve the AKS Terraform module and demonstrate the
full stack locally with Kind.

---

## Context

### Why AKS was in scope

AKS represents the natural progression from a managed workspace
(Databricks) to a managed Kubernetes control plane. It is one of the
required technologies in the original project scope, and it connects to
the observability story from Phase 5 (the Azure Monitor Workspace was
provisioned but never used).

### Why AKS was not provisioned

Unlike the previous phases, AKS has **continuous cost even when idle**:

| Component | Idle cost (30 days) |
|-----------|---------------------|
| Load Balancer (Standard) | ~$18 USD |
| Azure Container Registry (Basic) | ~$5 USD |
| Node pool (if provisioned) | $30-40 USD for one B2s node |

The Azure for Students subscription has a limited credit balance, and
provisioning AKS would consume the remaining credit in a few weeks without
producing lasting value for a portfolio.

Additional constraints apply:

- The subscription has a 6-vCPU regional quota.
- The Load Balancer alone is billed even with zero nodes.
- No billing method other than the student credit is available.

### Decision: preserve the module, demonstrate locally

Two decisions were made:

1. **Preserve the AKS Terraform module** in the repository, fully validated
   but commented out in the environment wiring. It can be activated by
   uncommenting the module and running `terraform apply`.

2. **Use Kind (Kubernetes in Docker) for demonstration.** Kind provides a
   real Kubernetes API server, scheduler, and controller manager. The
   manifests, Helm charts, Ingress, Prometheus, and Grafana are the same
   that would run on AKS. The only difference is the compute backend.

This is documented in [ADR-005](../architecture/adr-005-aks-local-first.md).

---

## Implementation

### 1. Terraform module for AKS (preserved, not applied)

Created `terraform/modules/aks/` with:

- `azurerm_kubernetes_cluster` with:
  - Free SKU (no control-plane cost)
  - Azure CNI network plugin
  - Calico network policy
  - System-assigned managed identity
  - System node pool with auto-scaling from 0 to 2
- `azurerm_kubernetes_cluster_node_pool` for application workloads
- Role assignments for ACR pull and Key Vault access

The module is validated with `terraform validate` but **commented out** in
`terraform/environments/dev/main.tf`. See the "Activation procedure"
section below.

### 2. FastAPI application

Created a new application under `python/src/api_server/`:

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness probe |
| `GET /ready` | Readiness probe (verifies Delta access) |
| `GET /metrics` | Prometheus metrics |
| `GET /series` | List available series |
| `GET /series/{name}/latest` | Latest month for a series |
| `GET /series/{name}/history` | Historical monthly data |
| `GET /summary` | Latest executive summary |

Structure:

```
python/src/api_server/
├── main.py
├── config.py
├── metrics.py          # Prometheus middleware
├── models/schemas.py
├── routers/
│   ├── health.py
│   ├── series.py
│   └── summary.py
└── services/
    ├── delta_reader.py
    └── spark_manager.py
```

### 3. Dockerfile

Multi-stage Dockerfile:

- **Builder stage:** installs Python dependencies into a venv
- **Runtime stage:** copies the venv, installs Java 21, creates a non-root
  user (UID 1000), copies the source code

**Adjustments made during build:**

- The base image `python:3.12-slim` now ships Debian 13 (Trixie), which
  replaced `openjdk-17` with `openjdk-21`. The Dockerfile was updated.
- The base was pinned to `slim-bookworm` (Debian 12) to avoid future
  breakage. This ensures reproducible builds.

### 4. Kind cluster

Kind cluster configuration:

- Single control-plane node
- Port mappings for HTTP (80) and HTTPS (443)
- `ingress-ready=true` label for NGINX scheduling
- **`extraMounts`** to map `python/spark-warehouse` from the host into
  the node at `/data/spark-warehouse`

The `extraMounts` was necessary because `hostPath` in Kubernetes refers to
the node's filesystem. In Kind, the "node" is a Docker container, so the
host path is not accessible without the bind mount.

### 5. NGINX Ingress Controller

Installed via the official Kind-specific manifest. NGINX is the most
common Ingress controller and is well documented.

### 6. Helm chart for the API

Created `kubernetes/helm/jc-sre-api/` with:

| Template | Purpose |
|----------|---------|
| `deployment.yaml` | Deployment with probes, resources, securityContext |
| `service.yaml` | ClusterIP service |
| `ingress.yaml` | NGINX Ingress pointing to `jc-sre.local` |
| `configmap.yaml` | Non-secret configuration |
| `serviceaccount.yaml` | Dedicated service account |

The chart supports:
- Liveness and readiness probes with configurable delays
- Resource requests and limits
- SecurityContext with `runAsNonRoot` and UID 1000
- Optional HPA (disabled by default)
- Configurable Delta Lake volume

### 7. Monitoring stack

Created `kubernetes/helm/jc-sre-monitoring/` as a wrapper chart with:

- **`kube-prometheus-stack`** as a Helm dependency (Prometheus Operator,
  Prometheus, Alertmanager, Grafana, Node Exporter, Kube State Metrics)
- **ServiceMonitor** for the API (automatic target discovery)
- **Grafana dashboard** provisioned via ConfigMap sidecar

The ServiceMonitor was corrected during implementation: the initial
selector used `app.kubernetes.io/name=jc-sre-databricks-api`, but the
actual Service has `app.kubernetes.io/name=jc-sre-api`.

### 8. Prometheus metrics middleware

Added `python/src/api_server/metrics.py` with a FastAPI middleware that
records:

- `http_requests_total` (Counter, by method, path, status)
- `http_request_duration_seconds` (Histogram, by method, path)
- `http_requests_in_progress` (Gauge, by method, path)

Dynamic path segments are normalized (`/series/selic` → `/series/{name}`)
to avoid cardinality explosion.

### 9. Grafana dashboard

Provisioned via ConfigMap. Contains seven panels:

| Panel | Type | Query |
|-------|------|-------|
| Request rate by endpoint | Time series | `sum by (path) (rate(http_requests_total[1m]))` |
| Request latency | Time series | `histogram_quantile` for p50, p95, p99 |
| Error rate (5xx) | Stat | Ratio of 5xx over total |
| Requests in progress | Stat | `sum(http_requests_in_progress)` |
| API memory usage | Stat | Container memory working set |
| Requests by status code | Time series | `sum by (status) (rate(http_requests_total[5m]))` |
| API container restarts | Stat | `kube_pod_container_status_restarts_total` |

### 10. Automation scripts

| Script | Purpose |
|--------|---------|
| `scripts/kind-setup.sh` | Creates Kind cluster + NGINX Ingress, generates config with `extraMounts` |
| `scripts/kind-teardown.sh` | Deletes the cluster |
| `scripts/kind-build-and-load.sh` | Builds Docker image and loads it into Kind |
| `scripts/kind-deploy.sh` | Deploys the API via Helm |
| `scripts/kind-monitoring-up.sh` | Installs the monitoring stack |

### 11. Makefile targets

Added under the "Kind" section:

```make
make kind-up              # Create cluster + NGINX
make kind-build           # Build + load API image
make kind-deploy          # Deploy API via Helm
make kind-monitoring      # Install Prometheus + Grafana
make kind-status          # Show cluster, pods, ingress
make kind-logs            # Tail API logs
make kind-down            # Delete cluster
```

---

## Validation

### Endpoints via Ingress

```bash
curl http://jc-sre.local/health
```

Response:

```json
{"status":"healthy","version":"0.1.0","timestamp":"..."}
```

```bash
curl http://jc-sre.local/series
```

Response: list of cdi, ipca, selic.

```bash
curl http://jc-sre.local/series/selic/latest
```

Response: latest month with values.

```bash
curl http://jc-sre.local/summary
```

Response: executive summary with `is_fallback=true`.

### Prometheus targets

All targets show **UP**, including:

- `serviceMonitor/jc-sre/jc-sre-api/0` — the API
- `serviceMonitor/jc-sre/jc-sre-monitoring-*` — the monitoring components

### Grafana dashboard

The dashboard **JC SRE API - Overview** displays:

- Request rate by endpoint (visible spike during test)
- Request latency (p50 ~50ms, p95 ~400ms, p99 ~800ms)
- Error rate (no 5xx during the test)
- API memory usage (~700 MiB, from PySpark)
- Requests by status code (200 only)

### Test suite

```bash
pytest tests/ -v
```

**Result:** 15 tests pass (10 previous + 5 new for the API server).

### Lint

```bash
ruff check src/ tests/
```

**Result:** All checks passed.

---

## Lessons Learned

### What worked well

- **Kind for local Kubernetes:** Running a real Kubernetes cluster on a
  laptop with the same manifests that would run on AKS demonstrates
  competence without cost.
- **ServiceMonitor:** Once the selector was corrected, target discovery
  worked automatically. Prometheus scrapes without manual configuration.
- **Grafana sidecar:** Dashboards provisioned via ConfigMap appear
  automatically in Grafana. No manual import required.
- **`extraMounts`:** The correct way to expose host directories to Kind
  nodes. Non-obvious but well-documented.

### Adjustments made

1. **Docker base image (Debian 13 → 12):** The `python:3.12-slim` tag
   moved from Debian 12 to 13, which replaced OpenJDK 17 with 21. The
   base was pinned to `slim-bookworm` (Debian 12) for reproducibility.
   See ADR-005.

2. **ServiceMonitor selector mismatch:** The initial ServiceMonitor used
   `jc-sre-databricks-api` as the label, but the actual Service has
   `jc-sre-api`. Fixed by aligning the selector with the Helm-generated
   labels.

3. **Spark permission error:** The `spark.py` module computed the
   warehouse directory from `__file__`, which produced the wrong path
   inside the container. Fixed by respecting the `DELTA_WAREHOUSE_PATH`
   environment variable.

4. **`.helmignore` breaking the chart:** An overly aggressive
   `.helmignore` prevented Helm from reading the `Chart.yaml`. The file
   was removed. Lesson: `.helmignore` should be conservative and
   well-tested.

5. **`hostPath` vs `extraMounts`:** The initial Deployment used
   `hostPath`, which points to the Docker container running the Kind
   node, not the host filesystem. Fixed by adding `extraMounts` to the
   Kind cluster configuration.

### What would be done differently

- **Validate ServiceMonitor labels before deploy.** A quick
   `kubectl get svc --show-labels` would have prevented the mismatch.
- **Pin Docker base images from the start.** Floating tags like
   `python:3.12-slim` are convenient but fragile.
- **Test the Helm chart in isolation before deploy.** `helm template`
   or `helm lint` would have caught the `.helmignore` issue earlier.

---

## Activation Procedure for AKS

When a subscription with sufficient credit and quota becomes available:

**Step 1: Uncomment the AKS module**

In `terraform/environments/dev/main.tf`:

```hcl
module "aks" {
  source = "../../modules/aks"

  resource_group_name     = azurerm_resource_group.main.name
  location                = var.location
  environment             = var.environment
  project_name            = var.project_name
  subnet_id               = module.networking.subnet_ids["aks"]
  kubernetes_version      = var.kubernetes_version
  node_vm_size            = var.node_vm_size
  node_min_count          = 0
  node_max_count          = 2
  workload_node_min_count = 0
  workload_node_max_count = 3
  acr_id                  = module.acr.registry_id
  key_vault_id            = module.keyvault.key_vault_id
  tags                    = var.tags
}
```

**Step 2: Uncomment the outputs**

```hcl
output "aks_cluster_name" {
  value = module.aks.cluster_name
}

output "aks_cluster_fqdn" {
  value = module.aks.cluster_fqdn
}
```

**Step 3: Provision the AKS cluster**

```bash
make terraform-apply
```

**Step 4: Configure kubectl**

```bash
az aks get-credentials \
  --resource-group dev-sredatabricks-rg \
  --name dev-sredatabricks-aks
```

**Step 5: Deploy the API via Helm**

```bash
helm upgrade --install jc-sre-api kubernetes/helm/jc-sre-api \
  --namespace jc-sre \
  --create-namespace \
  --wait
```

**Step 6: Deploy the monitoring stack**

```bash
helm upgrade --install jc-sre-monitoring kubernetes/helm/jc-sre-monitoring \
  --namespace jc-sre \
  --wait
```

**Step 7: Install an Ingress Controller**

NGINX Ingress via Helm:

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --wait
```

**Step 8: Get the Ingress public IP**

```bash
kubectl get svc -n ingress-nginx ingress-nginx-controller
```

Point your DNS or `/etc/hosts` to the external IP.

**No code changes are required.** The Helm charts, ServiceMonitor, and
dashboard work identically on Kind and AKS.

---

## Deactivation Procedure (Kind)

To remove the local Kubernetes environment:

```bash
make kind-down
```

This deletes the cluster and all workloads. The Docker image
`jc-sre-databricks-api:latest` remains in the local Docker daemon and can
be removed manually with `docker rmi` if desired.

---

## Artifacts

### Code

| Artifact | Path |
|----------|------|
| AKS Terraform module (preserved) | `terraform/modules/aks/` |
| API server | `python/src/api_server/` |
| Dockerfile | `python/Dockerfile` |
| `.dockerignore` | `python/.dockerignore` |
| API Helm chart | `kubernetes/helm/jc-sre-api/` |
| Monitoring Helm chart | `kubernetes/helm/jc-sre-monitoring/` |
| Grafana dashboard | `kubernetes/helm/jc-sre-monitoring/dashboards/api-overview.json` |
| Kind config (generated) | `kubernetes/kind/cluster-config.yaml` |
| Automation scripts | `scripts/kind-*.sh` |
| API tests | `python/tests/test_api_server.py` |

### Azure resources

None provisioned in this phase. The AKS module is preserved but not
applied.

### Local resources

| Resource | Type |
|----------|------|
| Kind cluster | `jc-sre-local` (1 control-plane node) |
| Namespace | `jc-sre` |
| API Deployment | `jc-sre-api` |
| Monitoring release | `jc-sre-monitoring` |
| Ingress | `jc-sre-api` (host: `jc-sre.local`) |
| Dashboard | `JC SRE API - Overview` |

---

## Next Phase

[Phase 9 — Disaster Recovery](../phases/phase-9-dr.md): implement backup
and recovery strategies for the data lake and pipeline.
