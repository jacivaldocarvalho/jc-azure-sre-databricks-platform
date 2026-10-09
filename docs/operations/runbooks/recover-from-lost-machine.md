# Runbook — Recover from a Lost Machine

Procedure for recovering the development environment after losing the
local machine (hardware failure, theft, reinstall, or migration).

---

## When to Use This Runbook

Use this runbook when:

- The developer's machine is lost or unusable
- A fresh OS install is required
- A new machine needs to be set up as a development environment
- A disaster recovery drill requires simulating the loss of the machine

**The good news:** almost everything is in Git or in the cloud. The
recovery is fast.

---

## Prerequisites

| Requirement | Notes |
|-------------|-------|
| Network access | To clone the Git repository and access Azure |
| GitHub access | The repository is public; any account can clone it |
| Azure credentials | The student account credentials (or a new account with access) |
| SSH key for Git | Optional; HTTPS works without it |

---

## What is Preserved

| Asset | Location | Recovery |
|-------|----------|----------|
| Source code | GitHub | `git clone` |
| Terraform state | Azure Storage | Accessed directly by Terraform |
| Secrets | Azure Key Vault | Accessed via Azure CLI |
| Data (Delta Lake) | Local (lost) | Regenerated via `make pipeline-run` |
| Local `.env` | Lost | Reconstructed from `.env.example` |
| Docker images | Local (lost) | Rebuilt via `make kind-build` |
| Kind cluster | Local (lost) | Recreated via `make kind-up` |
| ML models | N/A | Not applicable |

**Conclusion:** nothing irreplaceable is lost. The recovery is a matter
of re-installing tools and re-cloning the repository.

---

## Procedure

### Step 1: Install the required tools

On the new machine, install:

| Tool | Purpose | Installation |
|------|---------|--------------|
| Git | Version control | `sudo apt install git` |
| Python 3.12+ | Pipeline and API | `sudo apt install python3.12 python3.12-venv` |
| Java 17+ | PySpark runtime | `sudo apt install openjdk-17-jre-headless` |
| Terraform | Infrastructure | See terraform.io |
| Azure CLI | Cloud operations | See Microsoft docs |
| Docker | Containers | See docker.com |
| Kind | Local Kubernetes | See kind.sigs.k8s.io |
| kubectl | Kubernetes CLI | See kubernetes.io |
| Helm | Kubernetes package manager | See helm.sh |
| Make | Task automation | `sudo apt install make` |
| jq | JSON processing | `sudo apt install jq` |
| Ruff | Python linter | Installed via pip (in venv) |

### Step 2: Clone the repository

```bash
cd ~/projetos
git clone https://github.com/jacivaldocarvalho/jc-azure-sre-databricks-platform.git
cd jc-azure-sre-databricks-platform
```

### Step 3: Recreate the `.env` file

```bash
cp .env.example .env
```

Edit the `.env` file and add:

- `AZURE_KEY_VAULT_URI` (see `terraform output -raw key_vault_uri` after
  provisioning, or the value from the documentation)
- `AZURE_USE_CLI=true`

**Do not add** `AZURE_CLIENT_ID` or `AZURE_CLIENT_SECRET` — the project
uses Azure CLI authentication.

### Step 4: Authenticate with Azure

```bash
az login
az account set --subscription b4a10bfb-2a0e-43e7-bd50-ceb4624f160f
az account show --query "{User:user.name, Subscription:name}" -o table
```

**Expected:** the correct user and subscription are shown.

### Step 5: Configure Terraform variables

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` and provide the `subscription_id`.

### Step 6: Initialize the Python environment

```bash
cd ~/projetos/jc-azure-sre-databricks-platform
make pipeline-setup
```

This creates the virtualenv and installs dependencies.

**Alternative:**

```bash
cd python
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Step 7: Verify access to the Terraform state

```bash
cd terraform/environments/dev
terraform init
terraform plan
```

**Expected:**

- If the Azure environment exists: `No changes. Your infrastructure matches the configuration.`
- If the Azure environment was destroyed: `Plan: N to add, 0 to change, 0 to destroy.`

### Step 8: Re-provision the environment (if needed)

If the environment was destroyed, follow the
[Re-Provision the Environment](reprovision-environment.md) runbook.

### Step 9: Run the pipeline

```bash
cd ~/projetos/jc-azure-sre-databricks-platform/python
source .venv/bin/activate
python -m src.run_pipeline --start 2024-01-01 --end 2025-12-31
```

**Expected:** the pipeline runs successfully.

### Step 10: (Optional) Recreate the local Kubernetes cluster

```bash
cd ~/projetos/jc-azure-sre-databricks-platform
make kind-up
make kind-build
make kind-deploy
make kind-monitoring
```

**Expected:** the full local stack is running.

---

## Timing

| Phase | Estimated duration |
|-------|--------------------|
| Tool installation | 30-60 minutes |
| Clone + .env + auth | 5 minutes |
| Pipeline setup | 5 minutes |
| Verify Terraform state | 2 minutes |
| (Optional) Re-provision environment | 30-50 minutes |
| (Optional) Kind setup | 10 minutes |
| **Total (without optional)** | **~45 minutes** |
| **Total (with optional)** | **~2 hours** |

This is well within the RTO target of 8 hours.

---

## What is Not Recovered

| Item | Why | Impact |
|------|-----|--------|
| Local Spark warehouse | Regenerated by `make pipeline-run` | None |
| Docker images | Rebuilt by `make kind-build` | None |
| IDE settings | Personal preferences | Cosmetic |
| Shell history | Not tracked | Cosmetic |
| `~/.azure/` credentials | Re-authenticated via `az login` | None |

**Nothing of value is lost.**

---

## Prevention

- **Push to Git frequently.** The repository is the single source of truth.
- **Do not store secrets in local files.** Use the Key Vault.
- **Do not rely on local data.** The pipeline is reproducible.
- **Keep the `.env.example` up to date.** It documents what variables are needed.
- **Document the setup in the README.** Anyone should be able to replicate the environment.

---

## Testing

This runbook was validated in Phase 9, Sub-etapa 9.4 (partially — the
full recovery was simulated on the same machine). See
`docs/operations/dr-test-log.md`.

---

## Related Documents

- [Disaster Recovery Reference](../disaster-recovery.md)
- [Phase 9 — Disaster Recovery](../../phases/phase-9-dr.md)
- [Operations README](../README.md)
- [Re-Provision the Environment](reprovision-environment.md)

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial runbook |