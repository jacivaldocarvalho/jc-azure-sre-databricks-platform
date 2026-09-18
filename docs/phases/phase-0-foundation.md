# Phase 0 — Foundation

**Status:** Completed
**Duration:** Initial project setup
**Dependencies:** None

---

## Objective

Establish the operational and versioning foundation for the project before any cloud resource is provisioned. This phase ensures that all subsequent work follows consistent conventions and is fully auditable.

---

## Context

Before writing any infrastructure code, the project needed:

- A version-controlled repository with a clear branching strategy
- Standardized conventions for resource naming, tagging, and file organization
- A reproducible way to manage environment variables and secrets
- Task automation to reduce manual commands
- A directory structure that anticipates all future phases

Skipping this phase would result in ad-hoc decisions later, making the project harder to maintain and less professional.

---

## Implementation

### 1. Git Repository

- Initialized a Git repository with two base branches:
  - `main` — stable, production-ready code
  - `develop` — integration and development branch
- Adopted the branching model: `main`, `develop`, `feature/*`, `hotfix/*`

### 2. Project Conventions

Documented in `docs/conventions.md`:

- **Resource naming:** `{env}-{project}-{purpose}-{type}` (e.g., `dev-sredatabricks-rg`)
- **Git branches:** `main`, `develop`, `feature/*`, `hotfix/*`
- **Tags:** semantic versioning (`v1.0.0`)
- **Environment variables:** all secrets in `.env`, never committed
- **Makefile:** single source of truth for automation commands

### 3. Configuration Files

- `.gitignore` — patterns for Terraform, Python, Databricks, IDE, secrets
- `.env.example` — template with all expected environment variables
- `Makefile` — targets for `init`, `validate`, `format`, `clean`, `terraform-*`
- `README.md` — project overview, setup instructions, available commands
- `CONTRIBUTING.md`, `LICENSE` — standard project files

### 4. Directory Structure

```
jc-azure-sre-databricks-platform/
├── terraform/          # Infrastructure as Code
├── azure-devops/       # CI/CD Pipelines
├── databricks/         # Notebooks and Jobs
├── monitoring/         # Observability
├── security/           # RBAC and Policies
├── kubernetes/         # AKS Manifests
├── python/             # Python Code
├── scripts/            # Automation Scripts
└── docs/               # Documentation
```

Each directory has a clear purpose and will be populated as the phases progress.

---

## Validation

To validate this phase:

```bash
# Verify branch structure
git branch -a

# Verify files exist
ls -la | grep -E "\.gitignore|\.env\.example|Makefile|README\.md"

# Test Makefile
make help
make init

# Check that .env was created from .env.example
ls -la .env
```

**Expected results:**

1. Branches `main` and `develop` exist
2. All configuration files are present
3. `make help` lists available commands
4. `make init` creates `.env` from `.env.example`

---

## Lessons Learned

### What worked well

- Defining conventions early eliminated naming debates later
- The Makefile became the single entry point for all operations, reducing errors
- Separating `.env` from `.env.example` enforced the practice of not committing secrets from the very beginning

### Adjustments made

- Initially, the Makefile did not run `terraform init` automatically before `plan`. This was later found to be inconvenient when adding new modules. The decision to keep them separate was intentional (init is idempotent but slow) and remains.

---

## Artifacts

| Artifact | Path | Purpose |
|----------|------|---------|
| Conventions document | `docs/conventions.md` | Standards for the project |
| Git ignore | `.gitignore` | Files excluded from version control |
| Environment template | `.env.example` | Structure for credentials |
| Makefile | `Makefile` | Task automation |
| README | `README.md` | Project overview |
| Contribution guide | `CONTRIBUTING.md` | How to contribute |
| License | `LICENSE` | MIT |

---

## Next Phase

[Phase 1 — Base Network](phase-1-network.md): provision the foundational network infrastructure in Azure.
