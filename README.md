# JC-Azure SRE/Databricks Platform

Azure-Native SRE & Platform Engineering with Databricks and AI Integration

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC)](https://terraform.io)
[![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4)](https://azure.microsoft.com)
[![Databricks](https://img.shields.io/badge/Databricks-Premium-FF3621)](https://databricks.com)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-AKS-326CE5)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-2-blue)](https://github.com/jacivaldocarvalho/jc-azure-sre-databricks-platform)

## Project Status

**PHASE 2 - Databricks Workspace and Data Lake Completed**

| Phase | Description | Status |
|-------|-------------|--------|
| **PHASE 0** | Foundation: Git, Makefile, conventions, structure | Completed |
| **PHASE 1** | Base network: VNet, subnets, NSG, remote backend | Completed |
| **PHASE 2** | Databricks Workspace, ADLS Gen2, VNet Injection | Completed |
| **PHASE 3** | Data pipeline: notebooks, jobs, Delta Lake | Next |
| **PHASE 4** | CI/CD with Azure DevOps | Planned |
| **PHASE 5** | Observability: Prometheus, Grafana, SLOs | Planned |
| **PHASE 6** | Security: RBAC, Managed Identities, Key Vault | Planned |
| **PHASE 7** | AI Integration: Azure OpenAI, AI Foundry | Planned |
| **PHASE 8** | AKS and containerized workloads | Planned |
| **PHASE 9** | Disaster recovery and resilience | Planned |
| **PHASE 10** | Cost optimization and governance | Planned |

## Problem

Running production-grade data and AI workloads on Azure requires:

- Complex network segmentation and secure access to PaaS services
- Infrastructure as Code for reproducibility and auditability
- Observability tailored to data pipelines and ML workloads
- Cost control and FinOps practices
- Integration between data platforms and AI services
- SRE principles applied to cloud-native data infrastructure

Most projects address these challenges in isolation. This project demonstrates an integrated approach.

## Solution

JC-Azure SRE/Databricks Platform is a hands-on project that provisions and operates a complete Azure-native data and AI platform using SRE and DevOps practices.

**Key capabilities:**

- Infrastructure as Code with Terraform (modular, multi-environment)
- Network segmentation with Private Endpoints and delegation
- Databricks Workspace with VNet Injection (Premium tier)
- ADLS Gen2 for data lake with structured containers
- CI/CD pipelines with Azure DevOps
- Observability with Prometheus and Grafana
- Security with RBAC and Managed Identities
- Integration with Azure OpenAI and AI Foundry

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
| Ingest events from multiple sources | ADLS Gen2 containers (`raw`) with Event Hubs integration (Phase 3) |
| Process and enrich data continuously | Databricks notebooks and jobs with Delta Lake (Phase 3) |
| Train recommendation and churn models | Databricks ML runtime and MLflow tracking (Phase 3+) |
| Serve AI insights to business teams | Azure OpenAI and AI Foundry endpoints (Phase 7) |
| Ensure compliance and data protection | VNet Injection, Private Endpoints, RBAC, Key Vault (Phases 1, 2, 6) |
| Control costs during demand spikes | Databricks auto-termination, cluster policies, FinOps tagging (Phase 10) |
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

### Expected Outcomes

- Time from event to insight reduced from hours to minutes
- Recommendation model accuracy improved with fresher data
- Infrastructure cost predictability via tagging and cost allocation
- Compliance posture strengthened by private networking and RBAC
- Faster onboarding of new data sources and models
- Operational confidence through SLOs and proactive alerting




## Current Architecture (PHASE 2)

```
                         AZURE SUBSCRIPTION
                                │
                                ▼
                    ┌───────────────────────┐
                    │  dev-sredatabricks-rg │
                    │       (eastus)        │
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
└───────┬───────┘    │  Containers:     │    │  VNet Injection  │
        │            │    - raw         │    └────────┬─────────┘
        │            │    - processed   │             │
        │            │    - notebooks   │             │
        │            │    - checkpoints │             │
        │            └──────────────────┘             │
        │                                             │
        │                                             │
        ▼                                             ▼
┌────────────────────────────────────────────────────────────┐
│                      SUBNETS                               │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │  databricks  │  │  databricks  │  │     aks      │    │
│  │  10.0.1.0/24 │  │  _private    │  │ 10.0.2.0/24  │    │
│  │  (delegated) │  │  10.0.6.0/24 │  │              │    │
│  │              │  │  (delegated) │  │              │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │     data     │  │  monitoring  │  │   private    │    │
│  │  10.0.3.0/24 │  │  10.0.4.0/24 │  │  _endpoints  │    │
│  │              │  │              │  │  10.0.5.0/24 │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
│                                                            │
└────────────────────────────────────────────────────────────┘
                                │
                                ▼
                    ┌───────────────────────┐
                    │  NSG                  │
                    │  dev-sredatabricks    │
                    │  -nsg                 │
                    │  (restrictive default)│
                    └───────────────────────┘
```

## Planned Architecture (Complete)

```
                         INTERNET
                            │
                            ▼
                    ┌─────────────────┐
                    │  Azure Front   │
                    │  Door / App GW │
                    └────────┬───────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  AKS Cluster   │
                    │                │
                    │  Ingress       │
                    │  Services      │
                    │  Workloads     │
                    └────────┬───────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Databricks  │    │  ADLS Gen2   │    │  Azure       │
│  Workspace   │    │  Data Lake   │    │  OpenAI      │
│              │    │              │    │  + AI Foundry│
│  Notebooks   │    │  Delta Lake  │    │              │
│  Jobs        │    │  Unity Catalog│   │  Models      │
│  Clusters    │    │              │    │  Endpoints   │
└──────┬───────┘    └──────┬───────┘    └──────┬───────┘
       │                   │                   │
       └───────────────────┼───────────────────┘
                           │
                           ▼
                ┌──────────────────────┐
                │   OBSERVABILITY      │
                │                      │
                │  Prometheus │ Grafana │
                │  Loki       │ OTel    │
                │                      │
                │  SLIs / SLOs         │
                │  Alerting            │
                └──────────────────────┘


        ┌───────────────────────────────────────┐
        │              PLATFORM                 │
        │                                       │
        │  Azure DevOps  │ Terraform            │
        │  Key Vault     │ Managed Identities   │
        │  Policy        │ Cost Management      │
        └───────────────────────────────────────┘
```

## Implemented Features

### PHASE 0 - Foundation

- [x] Git repository with branching strategy (main/develop/feature/hotfix)
- [x] Makefile with task automation
- [x] .gitignore with patterns for Terraform, Python, Databricks, secrets
- [x] .env.example for environment variables
- [x] Project conventions documented (naming, tagging, structure)
- [x] Directory structure for all phases

### PHASE 1 - Base Network

- [x] Terraform remote backend on Azure Storage
- [x] Modular Terraform structure (networking module)
- [x] Resource Group with standardized naming
- [x] VNet with address space 10.0.0.0/16
- [x] Subnets for all planned workloads
- [x] Network Security Group with restrictive default rules
- [x] NSG associations with all subnets
- [x] Service endpoints for Storage and Key Vault
- [x] Multi-environment structure (dev, staging, prod)

### PHASE 2 - Databricks and Data Lake

- [x] Databricks Workspace (Premium tier)
- [x] VNet Injection with dedicated public and private subnets
- [x] Subnet delegation for Microsoft.Databricks/workspaces
- [x] Azure Data Lake Storage Gen2 (devsredata)
- [x] Four containers: raw, processed, notebooks, checkpoints
- [x] Hierarchical Namespace enabled
- [x] TLS 1.2 minimum
- [x] Blob public access disabled
- [x] Managed resource group for Databricks
- [x] Separate storage account for DBFS (devsredatadbw)

## Planned Features

- [ ] Data pipeline with notebooks and Delta Lake
- [ ] Scheduled Databricks jobs with monitoring
- [ ] Unity Catalog and metastore configuration
- [ ] Azure DevOps CI/CD pipelines
- [ ] Prometheus and Grafana observability stack
- [ ] SLIs and SLOs for critical services
- [ ] RBAC and Managed Identities
- [ ] Key Vault integration for secrets
- [ ] Azure OpenAI and AI Foundry integration
- [ ] AKS cluster and containerized workloads
- [ ] Disaster recovery strategy and runbooks
- [ ] Cost management and FinOps practices

## Prerequisites

Before getting started, install:

- Git
- Terraform >= 1.5.0
- Azure CLI
- Python >= 3.9
- Databricks CLI
- kubectl
- Make

You also need:

- An Azure subscription with sufficient permissions
- The Microsoft.Databricks provider registered
- A storage account for Terraform remote backend

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

> Important: Never commit the `.env` file.

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

### 5. Initialize and Deploy

```bash
make init
make terraform-init
make terraform-plan
make terraform-apply
```

## Make Commands

| Command | Description |
|---------|-------------|
| `make help` | Lists available commands |
| `make init` | Initializes the local project configuration |
| `make validate` | Validates Terraform configuration |
| `make format` | Formats Terraform and Python files |
| `make clean` | Removes temporary files |
| `make terraform-init` | Initializes Terraform (dev) |
| `make terraform-plan` | Generates execution plan (dev) |
| `make terraform-apply` | Applies infrastructure changes (dev) |
| `make terraform-destroy` | Destroys all managed resources (dev) |

> Warning: `terraform-apply` and `terraform-destroy` modify or remove Azure resources. Always review the plan before applying.

## Project Structure

```
jc-azure-sre-databricks-platform/
├── README.md
├── LICENSE
├── Makefile
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
├── azure-devops/
│   ├── pipelines/
│   └── templates/
│
├── databricks/
│   ├── notebooks/
│   │   ├── ingestion/
│   │   ├── processing/
│   │   ├── ml/
│   │   └── ai/
│   ├── jobs/
│   └── libraries/
│
├── monitoring/
│   ├── grafana/
│   ├── prometheus/
│   └── scripts/
│
├── security/
│   ├── access-control/
│   └── scripts/
│
├── kubernetes/
│   ├── manifests/
│   └── helm/
│
├── python/
│   └── src/
│
├── scripts/
│   ├── bootstrap.sh
│   ├── health-check.sh
│   └── rollback.sh
│
└── docs/
    ├── architecture/
    ├── operations/
    ├── troubleshooting/
    └── conventions.md
```

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

- `Environment`: dev, staging, prod
- `Project`: SRE-Databricks
- `ManagedBy`: Terraform

### Subnet Allocation

| Subnet | CIDR | Purpose |
|--------|------|---------|
| databricks | 10.0.1.0/24 | Databricks public subnet (delegated) |
| aks | 10.0.2.0/24 | AKS cluster nodes |
| data | 10.0.3.0/24 | Data services |
| monitoring | 10.0.4.0/24 | Prometheus and Grafana |
| private_endpoints | 10.0.5.0/24 | Private endpoints for PaaS |
| databricks_private | 10.0.6.0/24 | Databricks private subnet (delegated) |

## Environments

The infrastructure is organized into separate environments:

```text
terraform/
└── environments/
    ├── dev/          # Development environment
    ├── staging/      # Staging environment (future)
    └── prod/         # Production environment (future)
```

Each environment has its own Terraform configuration, state file, and variables. Currently only `dev` is implemented.

## Security

The following practices are maintained throughout development:

- Never commit the `.env` file
- Never store secrets directly in Terraform files
- Use Azure Key Vault for secrets management (planned for Phase 6)
- Use Managed Identities for resource access (planned for Phase 6)
- Follow the principle of least privilege
- NSG with restrictive default (deny all inbound, except Azure Load Balancer)
- TLS 1.2 minimum for storage accounts
- Blob public access disabled
- Hierarchical Namespace for ADLS Gen2

## Cost Management

To control costs during development:

- Databricks clusters configured with auto-termination
- Only necessary clusters active at any time
- All resources can be destroyed with `terraform destroy`
- Azure Cost Management for monitoring (planned)

## Documentation

Additional documentation is organized under `docs/`:

| Document | Description |
|----------|-------------|
| [Conventions](docs/conventions.md) | Project conventions and standards |
| [Architecture (Planned)](docs/architecture/) | Architecture decisions (ADRs) |
| [Operations (Planned)](docs/operations/) | Runbooks and procedures |
| [Troubleshooting (Planned)](docs/troubleshooting/) | Troubleshooting guides |

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **PHASE 0** | Foundation: Git, Makefile, conventions | Completed |
| **PHASE 1** | Base network: VNet, subnets, NSG | Completed |
| **PHASE 2** | Databricks Workspace and Data Lake | Completed |
| **PHASE 3** | Data pipeline with notebooks and Delta Lake | Next |
| **PHASE 4** | CI/CD with Azure DevOps | Planned |
| **PHASE 5** | Observability: Prometheus, Grafana, SLOs | Planned |
| **PHASE 6** | Security: RBAC, Managed Identities, Key Vault | Planned |
| **PHASE 7** | AI Integration: Azure OpenAI, AI Foundry | Planned |
| **PHASE 8** | AKS and containerized workloads | Planned |
| **PHASE 9** | Disaster recovery and resilience | Planned |
| **PHASE 10** | Cost optimization and governance | Planned |

## Contributing

1. Fork the project.
2. Create a branch for your feature (`git checkout -b feature/new-feature`).
3. Commit your changes (`git commit -m 'Add new feature'`).
4. Push to the branch (`git push origin feature/new-feature`).
5. Open a Pull Request.

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for more information.

## Author

**Jacivaldo Carvalho**
Telecommunications Engineer | DevOps | SRE | Networking

## Acknowledgments

- Microsoft Azure
- Terraform
- Databricks
- Azure DevOps
- Kubernetes
- Prometheus and Grafana
