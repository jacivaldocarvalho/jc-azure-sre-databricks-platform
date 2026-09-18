# JC-Azure SRE/Databricks Platform

Azure-Native SRE & Platform Engineering with Databricks and AI Integration

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC)](https://terraform.io)
[![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4)](https://azure.microsoft.com)
[![Databricks](https://img.shields.io/badge/Databricks-Premium-FF3621)](https://databricks.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-AKS-326CE5)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-3-blue)](https://github.com/jacivaldocarvalho/jc-azure-sre-databricks-platform)

---

## Project Status

**Phase 4 — CI/CD with Azure DevOps completed.**

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Foundation: Git, Makefile, conventions, structure | Completed |
| **Phase 1** | Base network: VNet, subnets, NSG, remote backend | Completed |
| **Phase 2** | Databricks Workspace, ADLS Gen2, VNet Injection, SCC | Completed |
| **Phase 3** | Data pipeline: ingestion, validation, transformation, Delta | Completed |
| **Phase 4** | CI/CD with Azure DevOps (YAML ready, execution pending billing) | Completed |
| **Phase 5** | Observability: Prometheus, Grafana, SLOs | Next |
| **Phase 6** | Security: RBAC, Managed Identities, Key Vault | Planned |
| **Phase 7** | AI Integration: Azure OpenAI, AI Foundry | Planned |
| **Phase 8** | AKS and containerized workloads | Planned |
| **Phase 9** | Disaster recovery and resilience | Planned |
| **Phase 10** | Cost optimization and governance | Planned |

---

## Problem

Running production-grade data and AI workloads on Azure requires:

- Complex network segmentation and secure access to PaaS services
- Infrastructure as Code for reproducibility and auditability
- Observability tailored to data pipelines and ML workloads
- Cost control and FinOps practices
- Integration between data platforms and AI services
- SRE principles applied to cloud-native data infrastructure

Most projects address these challenges in isolation. This project demonstrates an integrated approach.

---

## Solution

JC-Azure SRE/Databricks Platform provisions and operates a complete Azure-native data and AI platform using SRE and DevOps practices.

**Key capabilities:**

- Infrastructure as Code with Terraform (modular, multi-environment)
- Network segmentation with Private Endpoints and subnet delegation
- Databricks Workspace with VNet Injection and Secure Cluster Connectivity (Premium tier)
- ADLS Gen2 for data lake with structured containers
- Local-first data pipeline with PySpark and Delta Lake
- Ingestion from real public APIs (BCB SGS)
- Declarative schema validation with Pandera
- CI/CD pipelines with Azure DevOps (planned)
- Observability with Prometheus and Grafana (planned)
- Security with RBAC and Managed Identities (planned)
- Integration with Azure OpenAI and AI Foundry (planned)

---

## Real-World Use Case

### Scenario: Retail Company — Real-Time Customer Intelligence Platform

A mid-sized retail company with operations in multiple regions needs to:

- Ingest customer interaction events from e-commerce, mobile app, and physical stores
- Process and enrich data continuously for near real-time analytics
- Train recommendation and churn prediction models on historical data
- Serve AI-powered insights to business teams and downstream applications
- Maintain compliance with data protection regulations (LGPD/GDPR)
- Control costs while scaling with seasonal demand spikes

### How This Project Addresses the Scenario

| Business Need | Platform Capability |
|---------------|--------------------|
| Ingest events from multiple sources | ADLS Gen2 containers (`raw`) with Event Hubs integration (Phase 7+) |
| Process and enrich data continuously | PySpark pipeline with Delta Lake (Phase 3) |
| Train recommendation and churn models | Databricks ML runtime and MLflow (Phase 7+) |
| Serve AI insights to business teams | Azure OpenAI and AI Foundry endpoints (Phase 7) |
| Ensure compliance and data protection | VNet Injection, Private Endpoints, RBAC, Key Vault (Phases 1, 2, 6) |
| Control costs during demand spikes | Aggressive auto-termination, FinOps tagging (Phase 10) |
| Monitor pipeline and model health | Prometheus, Grafana, SLOs, alerting (Phase 5) |
| Automate deployment and rollback | Azure DevOps pipelines with Terraform (Phase 4) |

### Data Flow (Target State)

```
   ┌──────────────────────────────────────────────────────────────┐
   │                     DATA SOURCES                             │
   │                                                              │
   │  E-commerce   Mobile App   POS Systems   External APIs       │
   └───────┬────────────┬────────────┬────────────┬──────────────┘
           │            │            │            │
           └────────────┴─────┬──────┴────────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │   Azure Event Hubs  │
                    │   (Streaming)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Databricks         │
                    │  Workspace          │
                    │                     │
                    │  Ingest → Process   │
                    │  → Enrich           │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
      │  Delta Lake  │  │  ML Models   │  │  Azure       │
      │  (ADLS Gen2) │  │  (MLflow)    │  │  OpenAI      │
      │              │  │              │  │  + AI Foundry│
      └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  AKS Cluster        │
                    │                     │
                    │  REST APIs          │
                    │  Dashboards         │
                    │  Internal Tools     │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   BUSINESS USERS    │
                    │                     │
                    │  Analysts           │
                    │  Marketing          │
                    │  Operations         │
                    └─────────────────────┘
```

---

## Current Architecture (Phase 3)

```
                         AZURE SUBSCRIPTION
                                │
                                ▼
                    ┌───────────────────────┐
                    │  dev-sredatabricks-rg │
                    │      (brazilsouth)    │
                    └───────────┬───────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
        ▼                       ▼                       ▼
┌───────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  VNet         │    │  Storage Account │    │  Databricks      │
│  dev-sredat.. │    │  devsredata      │    │  Workspace       │
│  -vnet        │    │  (ADLS Gen2)     │    │  dev-sredat..    │
│  10.0.0.0/16  │    │                  │    │  -dbw (Premium)  │
└───────┬───────┘    │  Containers:     │    │  VNet + SCC      │
        │            │    - raw         │    └──────────────────┘
        │            │    - processed   │
        │            │    - notebooks   │
        │            │    - checkpoints │
        │            └──────────────────┘
        │
        ▼
┌────────────────────────────────────────────────────────────┐
│                      SUBNETS                               │
│  databricks │ databricks_private │ aks │ data │ monitoring │
│  private_endpoints                                         │
└────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  NSG                  │
                    │  dev-sredatabricks    │
                    │  -nsg (7 rules)       │
                    └───────────────────────┘
```

### Data Pipeline Architecture (Phase 3)

```
   ┌──────────────────────┐
   │  BCB SGS API         │
   │  (Selic, CDI, IPCA)  │
   └──────────┬───────────┘
              │ HTTP
              ▼
   ┌──────────────────────┐
   │  src/api/bcb_sgs.py  │
   │  Client with chunking│
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │  src/pipeline/       │
   │  ingest.py           │
   │  validate.py         │
   │  transform.py        │
   │  persist.py          │
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │  Delta Lake          │
   │  spark-warehouse/    │
   │    raw/              │
   │    processed/        │
   └──────────────────────┘
```

---

## Implemented Features

### Phase 0 — Foundation

- [x] Git repository with branching strategy
- [x] Makefile with task automation
- [x] `.gitignore` for Terraform, Python, Databricks, secrets
- [x] `.env.example` for environment variables
- [x] Project conventions documented
- [x] Directory structure for all phases

### Phase 1 — Base Network

- [x] Terraform remote backend on Azure Storage
- [x] Modular Terraform structure (`networking` module)
- [x] Resource Group with standardized naming
- [x] VNet with address space 10.0.0.0/16
- [x] Six subnets for planned workloads
- [x] NSG with documented rule set
- [x] NSG associations with all subnets
- [x] Service endpoints for Storage and Key Vault
- [x] Multi-environment structure (`dev`, `staging`, `prod`)

### Phase 2 — Databricks and Data Lake

- [x] Databricks Workspace (Premium tier)
- [x] VNet Injection with dedicated public and private subnets
- [x] Secure Cluster Connectivity (`no_public_ip = true`)
- [x] `NoAzureDatabricksRules` and pre-defined NSG rules
- [x] Subnet delegation for `Microsoft.Databricks/workspaces`
- [x] Azure Data Lake Storage Gen2 (`devsredata`)
- [x] Four containers: `raw`, `processed`, `notebooks`, `checkpoints`
- [x] Hierarchical Namespace enabled
- [x] TLS 1.2 minimum and blob public access disabled
- [x] Separate DBFS storage account (`devsredatadbw`)

### Phase 3 — Data Pipeline

- [x] API client for BCB SGS with automatic chunking
- [x] Ingestion of three economic series (Selic, CDI, IPCA)
- [x] Declarative validation with Pandera
- [x] Annualization, time dimensions, variation computation
- [x] Monthly aggregation per series
- [x] Delta Lake persistence (raw and processed layers)
- [x] Local-first execution with PySpark
- [x] Test suite with 10 unit and smoke tests
- [x] Automated local environment setup

---

## CI/CD

The project includes Azure DevOps pipeline definitions that automate validation, testing, and deployment:

- **Terraform pipeline** — validates formatting, runs `terraform plan`, publishes the plan as an artifact, and applies under manual approval via an Environment
- **Python pipeline** — runs Ruff for linting, executes the test suite with coverage, and publishes test results and coverage reports

Both pipelines use reusable templates (under `azure-devops/templates/`) and path filters to avoid unnecessary runs.

### Authentication

Authentication uses **Workload Identity Federation (OIDC)**. No secrets are stored in Azure DevOps. Tokens are issued per pipeline run and validated by Azure AD against a Federated Credential.

### Execution limitation

The pipelines are implemented, versioned, and ready to run, but could not be executed on Microsoft-hosted agents. Azure DevOps does not grant the free hosted parallel job to new organizations without billing, and the **Azure for Students** subscription is not eligible for Azure DevOps billing.

A self-hosted agent was considered and rejected: it would make the repository dependent on a specific personal machine, which is not appropriate for a public portfolio.

The same validation performed by the pipelines is available locally through `make` targets (`make validate`, `make lint`, `make pipeline-test`). The pipelines can be activated on any Azure DevOps organization with a Pay-As-You-Go subscription by simply registering them in the UI.

See [Phase 4 — CI/CD](docs/phases/phase-4-cicd.md) for details.

---

## Planned Features

- [ ] CI/CD with Azure DevOps (Phase 4)
- [ ] Prometheus and Grafana observability stack (Phase 5)
- [ ] SLIs and SLOs for critical services (Phase 5)
- [ ] RBAC and Managed Identities (Phase 6)
- [ ] Key Vault integration for secrets (Phase 6)
- [ ] Azure OpenAI and AI Foundry integration (Phase 7)
- [ ] AKS cluster and containerized workloads (Phase 8)
- [ ] Disaster recovery strategy and runbooks (Phase 9)
- [ ] Cost management and FinOps practices (Phase 10)

---

## Prerequisites

Before getting started, install:

- Git
- Terraform >= 1.5.0
- Azure CLI
- Python 3.12+ (for local pipeline)
- Java 17 (for PySpark)
- Databricks CLI
- kubectl
- Make

You also need:

- An Azure subscription with sufficient permissions
- The `Microsoft.Databricks` provider registered
- A storage account for the Terraform remote backend

**Known limitation:** Azure for Students subscriptions cannot provision Databricks clusters due to quota and SKU restrictions. See [ADR-001](docs/architecture/adr-001-databricks-cluster-limitation.md).

---

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/jacivaldocarvalho/jc-azure-sre-databricks-platform.git
cd jc-azure-sre-databricks-platform
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
# Edit .env with your Azure credentials
```

### 3. Configure Terraform Variables

```bash
cd terraform/environments/dev
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your subscription_id
```

### 4. Authenticate with Azure

```bash
az login
az account set --subscription <subscription-id>
```

### 5. Provision the Infrastructure

```bash
make terraform-init
make terraform-plan
make terraform-apply
```

### 6. Set Up the Local Pipeline

```bash
make pipeline-setup
```

### 7. Run the Pipeline

```bash
make pipeline-run
```

### 8. Inspect the Results

```bash
make pipeline-query
```

---

## Make Commands

### Project

| Command | Description |
|---------|-------------|
| `make help` | List all available commands |
| `make init` | Initialize project (create `.env` from example) |
| `make validate` | Validate Terraform configuration |
| `make format` | Format Terraform and Python files |
| `make lint` | Run Ruff linter on Python code |
| `make clean` | Clean temporary files and caches |

### Terraform (dev environment)

| Command | Description |
|---------|-------------|
| `make terraform-init` | Initialize Terraform |
| `make terraform-plan` | Plan infrastructure changes |
| `make terraform-apply` | Apply infrastructure changes |
| `make terraform-destroy` | Destroy all managed resources |

### Data Pipeline

| Command | Description |
|---------|-------------|
| `make pipeline-setup` | Create virtualenv and install dependencies |
| `make pipeline-test` | Run pipeline unit tests |
| `make pipeline-run` | Execute the pipeline with default date range |
| `make pipeline-query` | Query the monthly aggregates Delta table |
| `make pipeline-clean` | Remove local Delta tables and caches |

> **Warning:** `terraform-apply` and `terraform-destroy` modify or remove Azure resources. Always review the plan before applying.

---

## Project Structure

```
jc-azure-sre-databricks-platform/
├── README.md
├── LICENSE
├── Makefile
├── CONTRIBUTING.md
├── .gitignore
├── .env.example
│
├── terraform/
│   ├── modules/
│   │   ├── networking/       # VNet, subnets, NSG
│   │   ├── datalake/         # ADLS Gen2 and containers
│   │   └── databricks/       # Workspace with VNet Injection
│   └── environments/
│       ├── dev/
│       ├── staging/
│       └── prod/
│
├── python/
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── src/
│   │   ├── api/              # BCB SGS client
│   │   ├── pipeline/         # ingest, validate, transform, persist
│   │   └── utils/            # logging, spark helpers
│   └── tests/                # 10 unit and smoke tests
│
├── databricks/
│   ├── notebooks/
│   ├── jobs/
│   └── libraries/
│
├── azure-devops/
│   ├── pipelines/
│   └── templates/
│
├── monitoring/
├── security/
├── kubernetes/
├── scripts/
│   └── setup-local.sh
│
└── docs/
    ├── README.md
    ├── conventions.md
    ├── phases/
    │   ├── phase-0-foundation.md
    │   ├── phase-1-network.md
    │   ├── phase-2-databricks-data-lake.md
    │   └── phase-3-pipeline.md
    ├── architecture/
    │   ├── README.md
    │   └── adr-001-databricks-cluster-limitation.md
    ├── operations/
    │   └── README.md
    └── troubleshooting/
        └── README.md
```

---

## Infrastructure Overview

### Naming Convention

| Resource | Pattern | Example |
|----------|---------|---------|
| Resource Group | `{env}-{project}-{purpose}-rg` | `dev-sredatabricks-rg` |
| VNet | `{env}-{project}-vnet` | `dev-sredatabricks-vnet` |
| Subnet | `{env}-{project}-{type}-subnet` | `dev-sredatabricks-data-subnet` |
| Storage Account | `{env}{project}{purpose}` | `devsredata` |
| Databricks | `{env}-{project}-dbw` | `dev-sredatabricks-dbw` |

### Tags

All resources are tagged with:

- `Environment`: `dev`, `staging`, `prod`
- `Project`: `SRE-Databricks`
- `ManagedBy`: `Terraform`

### Subnet Allocation

| Subnet | CIDR | Purpose |
|--------|------|---------|
| databricks | 10.0.1.0/24 | Databricks public subnet (delegated) |
| aks | 10.0.2.0/24 | AKS cluster nodes (future) |
| data | 10.0.3.0/24 | Data services |
| monitoring | 10.0.4.0/24 | Prometheus and Grafana (future) |
| private_endpoints | 10.0.5.0/24 | Private endpoints for PaaS |
| databricks_private | 10.0.6.0/24 | Databricks private subnet (delegated) |

---

## Documentation

Detailed documentation is available under `docs/`:

| Document | Description |
|----------|-------------|
| [Documentation Index](docs/README.md) | Entry point for all documentation |
| [Conventions](docs/conventions.md) | Project standards and conventions |
| [Phase 0 — Foundation](docs/phases/phase-0-foundation.md) | Project setup |
| [Phase 1 — Base Network](docs/phases/phase-1-network.md) | Network provisioning |
| [Phase 2 — Databricks and Data Lake](docs/phases/phase-2-databricks-data-lake.md) | Platform provisioning |
| [Phase 3 — Data Pipeline](docs/phases/phase-3-pipeline.md) | Pipeline implementation |
| [Phase 4 — CI/CD](docs/phases/phase-4-cicd.md) | Azure DevOps pipelines and templates |
| [ADR-001](docs/architecture/adr-001-databricks-cluster-limitation.md) | Databricks cluster limitation |
| [Operations](docs/operations/README.md) | Runbooks and procedures |
| [Troubleshooting](docs/troubleshooting/README.md) | Known issues and fixes |

---

## Security

The following practices are maintained throughout development:

- Never commit the `.env` file
- Never store secrets directly in Terraform files
- Azure Key Vault for secrets management (planned for Phase 6)
- Managed Identities for resource access (planned for Phase 6)
- Principle of least privilege for Azure permissions
- NSG with restrictive default and documented exceptions
- TLS 1.2 minimum for storage accounts
- Blob public access disabled
- Hierarchical Namespace for ADLS Gen2
- Secure Cluster Connectivity for Databricks
- `NoAzureDatabricksRules` with pre-defined NSG rules

---

## Cost Management

The project runs on a constrained budget. Controls in place:

- Databricks clusters with aggressive auto-termination (when provisionable)
- Only necessary resources kept active
- All resources can be destroyed with `make terraform-destroy`
- Data pipeline runs locally, avoiding compute costs in the cloud
- Azure Cost Management for monitoring (planned for Phase 10)

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Foundation: Git, Makefile, conventions | Completed |
| **Phase 1** | Base network: VNet, subnets, NSG | Completed |
| **Phase 2** | Databricks Workspace and Data Lake | Completed |
| **Phase 3** | Data pipeline with ingestion, validation, Delta | Completed |
| **Phase 4** | CI/CD with Azure DevOps | Completed |
| **Phase 5** | Observability: Prometheus, Grafana, SLOs | Next |
| **Phase 6** | Security: RBAC, Managed Identities, Key Vault | Planned |
| **Phase 7** | AI Integration: Azure OpenAI, AI Foundry | Planned |
| **Phase 8** | AKS and containerized workloads | Planned |
| **Phase 9** | Disaster recovery and resilience | Planned |
| **Phase 10** | Cost optimization and governance | Planned |

---

## Contributing

1. Fork the project.
2. Create a branch for your feature (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.

See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

---

## Author

**Jacivaldo Carvalho**
Telecommunications Engineer | DevOps | SRE | Networking

---

## Acknowledgments

- Microsoft Azure
- Terraform
- Databricks
- Banco Central do Brasil (public data)
- PySpark and Delta Lake communities
- Prometheus and Grafana
- Kubernetes