# JC-Azure SRE/Databricks Platform

Azure-Native SRE & Platform Engineering with Databricks and AI Integration

[![Terraform](https://img.shields.io/badge/Terraform-%3E%3D1.5-7B42BC)](https://terraform.io)
[![Azure](https://img.shields.io/badge/Azure-Cloud-0078D4)](https://azure.microsoft.com)
[![Databricks](https://img.shields.io/badge/Databricks-Premium-FF3621)](https://databricks.com)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB)](https://python.org)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-AKS-326CE5)](https://kubernetes.io)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Phase](https://img.shields.io/badge/Phase-7-blue)](https://github.com/jacivaldocarvalho/jc-azure-sre-databricks-platform)

---

## Project Status

**Phase 7 — AI Integration completed (with documented limitation).**

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Foundation: Git, Makefile, conventions, structure | Completed |
| **Phase 1** | Base network: VNet, subnets, NSG, remote backend | Completed |
| **Phase 2** | Databricks Workspace, ADLS Gen2, VNet Injection, SCC | Completed |
| **Phase 3** | Data pipeline: ingestion, validation, transformation, Delta | Completed |
| **Phase 4** | CI/CD with Azure DevOps (code ready, execution blocked by billing) | Completed |
| **Phase 5** | Observability: SLIs/SLOs, Application Insights, alerts | Completed |
| **Phase 6** | Security: Key Vault, RBAC, Managed Identities, cleanup | Completed |
| **Phase 7** | AI Integration: executive summaries with fallback strategy | Completed |
| **Phase 8** | AKS and containerized workloads | Next |

---

## Problem

Provisioning a data platform on Azure while respecting SRE principles requires solving several challenges simultaneously:

- **Infrastructure as Code** that is modular, auditable, and portable across environments
- **Network segmentation** with private endpoints, delegated subnets, and service endpoints
- **Secure authentication** without long-lived secrets (OIDC, Managed Identity)
- **Observability** defined by SLIs and SLOs, not by the tools that happen to be available
- **Cost control** under a constrained budget (Azure for Students)
- **Documented trade-offs** when the platform imposes limitations that cannot be worked around

Most SRE portfolios show isolated pieces of these challenges: a Terraform file, a CI/CD pipeline, a dashboard. This project demonstrates how they integrate.

---

## Solution

A modular Azure platform built with Terraform, complemented by a Python data pipeline using PySpark and Delta Lake, and instrumented for observability. The project prioritizes:

- **Infrastructure as Code** — 7 Terraform modules with remote state, multi-environment structure, and reproducible provisioning
- **Security by design** — Key Vault for secrets, Managed Identity for service-to-service authentication, RBAC with least privilege, and no shared account keys
- **SLO-driven observability** — SLIs and SLOs defined before any tool was chosen
- **Documented limitations** — ADRs explain every significant decision, including what could not be delivered and why
- **Local-first development** — the data pipeline runs and is tested locally before any cloud dependency
- **Data engineering** — a functional pipeline ingesting real data from the Brazilian Central Bank, validated with Pandera, transformed with PySpark, and persisted in Delta Lake
- **AI integration** — executive summary generation with a fallback strategy for environments where Azure OpenAI is not provisionable

The project intentionally does not attempt to be a production platform. It is a demonstration of professional engineering practices applied to a realistic scenario, executed under the constraints of an Azure for Students subscription.

---

## Applicability

The patterns demonstrated in this project apply to a range of real-world scenarios.

### Patterns and where they apply

| Pattern | Applies to |
|---------|-----------|
| Modular Terraform with remote state | Any Azure project with multiple environments |
| VNet Injection for managed services | Any Databricks, Synapse, or managed compute deployment |
| Zero-secret authentication (OIDC + Managed Identity) | Any organization moving away from API keys and static credentials |
| SLO-driven observability | Any team that wants meaningful alerts instead of dashboard noise |
| Documented ADRs with alternatives | Any project where technical decisions need to survive turnover |
| Fallback strategies for restricted environments | Any developer on a constrained subscription or sandbox |

### When this project is directly applicable

- A small team starting an Azure data platform from scratch
- An SRE/DevOps engineer who needs a reference implementation for Databricks VNet Injection with SCC
- A developer learning how to build zero-secret authentication flows with OIDC and Managed Identity
- A team transitioning from ad-hoc infrastructure to Terraform with proper module boundaries
- Anyone who needs a reference for documenting platform limitations honestly

### When it is not applicable

This is not a production-ready blueprint for the following scenarios:

- **Production-scale streaming pipelines** — would require Event Hubs or Kafka, which are not part of this project
- **Multi-region deployments** — would require Traffic Manager, geo-replication, and cross-region state management
- **Enterprise compliance** — would require Defender for Cloud, Azure Policy, SIEM integration, and continuous audit
- **High-throughput data processing** — the pipeline is designed for batch jobs with modest data volumes
- **MLOps at scale** — the AI integration is a demonstration, not an ML platform

The distinction is intentional: the project is honest about its scope.

---

## Current State vs. Target State

The project was designed as a multi-phase initiative. Due to limitations of the Azure for Students subscription, some phases could not be fully executed. The table below shows what was delivered and what remains.

| Capability | Designed | Delivered | Notes |
|-----------|----------|-----------|-------|
| Terraform modules | 7 | **7** | All validated |
| Network segmentation | Yes | **Yes** | 6 subnets, delegations, service endpoints |
| Databricks VNet Injection | Yes | **Yes** | SCC, `NoAzureDatabricksRules` |
| Data pipeline (batch) | Yes | **Yes** | PySpark + Delta, 10 tests passing |
| Security (Key Vault, MI, RBAC) | Yes | **Yes** | Zero-secret authentication |
| Observability (SLIs/SLOs) | Yes | **Yes** | Application Insights, workbook, 4 alerts |
| AI integration | Yes | **Code ready** | Fallback strategy in use; Azure OpenAI not provisionable |
| CI/CD pipelines | Yes | **Code only** | Cannot execute (billing restriction) |
| Databricks cluster | Yes | **No** | SKU not available on for Students |
| Azure OpenAI | Yes | **Code only** | Quota restriction on for Students |
| AKS cluster | Planned | **No** | Not started (Phase 8) |
| Disaster recovery | Planned | **No** | Not started (Phase 9) |
| Cost optimization | Planned | **No** | Not started (Phase 10) |

### What is fully functional

- Terraform infrastructure (all modules provision correctly)
- Local data pipeline (runs end-to-end with real data)
- Observability (metrics flow to Application Insights, alerts are configured)
- Security model (Key Vault, Managed Identity, RBAC all active)

### What is implemented but not executable in the current environment

- **CI/CD pipelines** — the YAML is complete and validated. Execution requires a Pay-As-You-Go subscription for Azure DevOps billing.
- **Azure OpenAI integration** — the Terraform module and Python client are ready. Provisioning requires a subscription with Azure OpenAI quota.

### What has not been started

- AKS workloads, disaster recovery, and cost optimization (Phases 8, 9, 10).

This transparency is intentional. The ADRs document the reasoning behind each limitation.

---

## Target Architecture (Complete Vision)

The diagram below represents the **full target architecture** if all phases were completed. In the current environment, only the components in the left half (through Phase 7) are operational.

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
                    │   Azure Event Hubs  │   [Not implemented]
                    │   (Streaming)       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Databricks         │   [Workspace provisioned]
                    │  Workspace          │   [Cluster not provisionable]
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
      ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
      │  Delta Lake  │  │  ML Models   │  │  Azure       │
      │  (ADLS Gen2) │  │  (MLflow)    │  │  OpenAI      │
      │  [Operational]│ │ [Not started]│  │  [Code only] │
      └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
             │                 │                 │
             └─────────────────┼─────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  AKS Cluster        │   [Phase 8]
                    │                     │
                    │  REST APIs          │
                    │  Dashboards         │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │   BUSINESS USERS    │
                    └─────────────────────┘
```

---

## Current Architecture (Phase 7)

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
        │            │    - summaries   │
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

        Additional services (active):
        - Key Vault (dev-sredatabricks-kv)
        - Managed Identity (dev-sredatabricks-dbw-mi)
        - Application Insights (dev-sredatabricks-ai)
        - Log Analytics (dev-sredatabricks-law)
        - Azure Monitor Workspace (dev-sredatabricks-amw)
```

### Data Pipeline Architecture (Phase 3 + Phase 7)

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
   │  AI summary          │
   │  src/ai/             │
   │  (client + fallback) │
   └──────────┬───────────┘
              │
              ▼
   ┌──────────────────────┐
   │  Delta Lake          │
   │  spark-warehouse/    │
   │    raw/              │
   │    processed/        │
   │      - variations    │
   │      - monthly_agg   │
   │      - summaries     │
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

### Phase 4 — CI/CD with Azure DevOps

- [x] Workload Identity Federation (OIDC) — no secrets in Azure DevOps
- [x] Terraform pipeline with validate, plan, and apply stages
- [x] Python pipeline with lint, test, and coverage
- [x] Reusable YAML templates for each stage
- [x] Path filters to avoid unnecessary runs
- [x] Manual approval gate for Terraform apply via Azure DevOps Environment
- [x] Branch policies and environment configuration
- [x] Documented execution limitation (Azure for Students cannot enable billing)

### Phase 5 — Observability

- [x] SLIs and SLOs defined before choosing tools (`monitoring/slos.md`)
- [x] Error budget policy with tiered operational actions
- [x] OpenTelemetry instrumentation across all pipeline modules
- [x] Seven metric instruments exposed (counters, histograms, up-down counter)
- [x] Application Insights as metrics backend
- [x] Log Analytics Workspace for backend storage
- [x] Workbook `Pipeline Overview` with five panels
- [x] Four SLO-aligned alert rules (failure, stale data, low volume, slow)
- [x] Action group `sre-oncall` for email notifications
- [x] ADR-002 documenting the observability stack selection

### Phase 6 — Security

- [x] Azure Key Vault with RBAC authorization
- [x] Application Insights connection string migrated to Key Vault
- [x] Pipeline resolves secrets from Key Vault at runtime
- [x] `AzureCliCredential` locally, `DefaultAzureCredential` in Azure
- [x] User-Assigned Managed Identity for Databricks
- [x] Databricks Managed Identity has `Storage Blob Data Contributor` on the Data Lake
- [x] Databricks Managed Identity has `Key Vault Secrets User` on the Key Vault
- [x] Azure DevOps Service Principal scope reduced from Subscription to Resource Group
- [x] Legacy Service Principal removed (Contributor at subscription + orphan secret)
- [x] Security model documented in `docs/architecture/security-model.md`
- [x] ADR-003 documenting the security decisions

### Phase 7 — AI Integration

- [x] Executive summary use case selected from five candidates
- [x] Terraform module for Azure OpenAI (`gpt-4o-mini`, GlobalStandard)
- [x] Role assignment for Managed Identity on OpenAI (conditional)
- [x] AI client abstraction (`python/src/ai/client.py`)
- [x] Deterministic fallback generator (`python/src/ai/fallback.py`)
- [x] Prompt templates kept separate (`python/src/ai/prompts.py`)
- [x] Summary orchestration (`python/src/ai/summarizer.py`)
- [x] Pipeline integration (Steps 5b and 6b)
- [x] Delta persistence (`processed/summaries`)
- [x] Centralized credential resolution (`utils/credentials.py`)
- [x] ADR-004 documenting the strategy and activation procedure
- [x] Documented limitation: Azure for Students cannot provision Azure OpenAI quota

---

## Planned Features

The following phases have not been started:

- [ ] AKS cluster and containerized workloads (Phase 8)
- [ ] Disaster recovery strategy and runbooks (Phase 9)
- [ ] Cost management and FinOps practices (Phase 10)

### Improvements pending subscription upgrade

If the subscription is upgraded to Pay-As-You-Go, the following become possible:

- [ ] Execute Azure DevOps pipelines on Microsoft-hosted agents
- [ ] Provision a Databricks cluster for pipeline execution
- [ ] Provision and use Azure OpenAI for AI-generated summaries
- [ ] Migrate Workbook and Alert Rules from manual creation to Terraform

None of these require code changes. The infrastructure and pipeline code
are ready to be activated.

---

## CI/CD

The project includes Azure DevOps pipeline definitions that automate validation, testing, and deployment:

- **Terraform pipeline** — validates formatting, runs `terraform plan`, publishes the plan as an artifact, and applies under manual approval via an Environment
- **Python pipeline** — runs Ruff for linting, executes the test suite with coverage, and publishes test results and coverage reports

Both pipelines use reusable templates (under `azure-devops/templates/`) and path filters to avoid unnecessary runs.

### Authentication

Authentication uses **Workload Identity Federation (OIDC)**. No secrets are stored in Azure DevOps. Tokens are issued per pipeline run and validated by Microsoft Entra ID against a Federated Credential.

### Execution limitation

The pipelines are implemented, versioned, and ready to run, but could not be executed on Microsoft-hosted agents. Azure DevOps does not grant the free hosted parallel job to new organizations without billing, and the **Azure for Students** subscription is not eligible for Azure DevOps billing.

A self-hosted agent was considered and rejected: it would make the repository dependent on a specific personal machine, which is not appropriate for a public portfolio.

The same validation performed by the pipelines is available locally through `make` targets (`make validate`, `make lint`, `make pipeline-test`). The pipelines can be activated on any Azure DevOps organization with a Pay-As-You-Go subscription by simply registering them in the UI.

See [Phase 4 — CI/CD](docs/phases/phase-4-cicd.md) for details.

---

## Observability

The pipeline emits metrics on every execution to **Application Insights**, and the SLIs/SLOs are defined in `monitoring/slos.md` before any tool was chosen.

### Defined SLOs

| SLI | SLO | Window |
|-----|-----|--------|
| Pipeline availability | 99% | 30 days |
| Execution latency (P95) | < 120s | 7 days |
| Validation error rate | < 1% | 30 days |
| Data freshness | < 24h | Continuous |
| Processed volume | > 1000 records | Per run |

### Metrics

Seven instruments are emitted via OpenTelemetry:

- `pipeline_runs_total` (Counter, by status)
- `pipeline_rows_processed_total` (Counter, by series and stage)
- `pipeline_rows_rejected_total` (Counter, by reason)
- `pipeline_api_requests_total` (Counter, by series and status)
- `pipeline_duration_seconds` (Histogram, by stage)
- `pipeline_api_request_duration_seconds` (Histogram, by series)
- `pipeline_last_success_timestamp` (UpDownCounter)

### Visualization and alerting

- A Workbook `Pipeline Overview` in Application Insights renders five panels covering all SLIs
- Four alert rules are configured, aligned with the SLOs: `pipeline-failure`, `pipeline-data-stale`, `pipeline-low-volume`, `pipeline-slow`
- Alerts notify the `sre-oncall` action group via email

### Architectural decision

The original plan was to use Azure Monitor managed Prometheus with Grafana. During implementation, it became clear that the official Microsoft SDK (`azure-monitor-opentelemetry-exporter`) sends metrics to Application Insights, not to the managed Prometheus endpoint. The pipeline uses **Application Insights** as the metrics backend. This is documented in [ADR-002](docs/architecture/adr-002-observability-stack.md).

The Workbook and alert rules were created manually in the portal for iteration speed and are documented in the [Post-apply checklist](docs/operations/README.md). Migration to Terraform is planned for a later phase.

See [Phase 5 — Observability](docs/phases/phase-5-observability.md) for details.

---

## Security

The project adopts a least-privilege posture with zero long-lived secrets for service-to-service authentication.

### Authentication flows

| Flow | Identity | Mechanism |
|------|----------|-----------|
| Local development | Operator | `az login` (Azure CLI) |
| CI/CD (Azure DevOps) | Service Principal | Workload Identity Federation (OIDC) |
| Databricks runtime | User-Assigned Managed Identity | Managed Identity |
| Pipeline secrets | Key Vault | RBAC-authorized access |
| AI invocation (when enabled) | Managed Identity / Azure CLI | Microsoft Entra ID |

### Least privilege in practice

| Identity | Scope |
|----------|-------|
| Azure DevOps Service Principal | Contributor at the project Resource Group |
| Databricks Managed Identity | Key Vault Secrets User on the Key Vault |
| Databricks Managed Identity | Storage Blob Data Contributor on the Data Lake |
| Databricks Managed Identity | Cognitive Services OpenAI User (conditional) |
| Operator | Key Vault Administrator on the Key Vault |

### Key Vault

Secrets are centralized in Azure Key Vault `dev-sredatabricks-kv` with RBAC-based access. The pipeline resolves the Application Insights connection string from Key Vault at runtime, using `AzureCliCredential` locally (via `AZURE_USE_CLI=true`) and `DefaultAzureCredential` in Azure.

### Cleanup performed in Phase 6

A legacy Service Principal with Contributor at the subscription scope was identified and removed, along with its client secret. This eliminated an orphaned credential that had caused a real security incident during local development.

### Best practices maintained

- Never commit the `.env` file
- Never store secrets in Terraform files
- Use Key Vault for all secrets
- Use Managed Identity for service-to-service authentication
- Apply least privilege to every role assignment
- Maintain a restrictive NSG with documented exceptions
- Use TLS 1.2 minimum and disable public blob access
- Enable Hierarchical Namespace for ADLS Gen2
- Use Secure Cluster Connectivity for Databricks

The full security posture is documented in [docs/architecture/security-model.md](docs/architecture/security-model.md). The architectural decisions are captured in [ADR-003](docs/architecture/adr-003-security-model.md).

See [Phase 6 — Security](docs/phases/phase-6-security.md) for the implementation record.

---

## AI Integration

The pipeline generates an executive summary of Brazilian economic indicators after each aggregation step. The summary is persisted in Delta (`processed/summaries`) with metadata about the model used.

### Architecture

```
                Pipeline executes
                       │
                       ▼
             ┌───────────────────┐
             │  Monthly           │
             │  aggregates ready  │
             └─────────┬─────────┘
                       │
                       ▼
             ┌───────────────────┐
             │  AI client         │
             │  (client.py)       │
             └─────────┬─────────┘
                       │
              ┌────────┴────────┐
              │                 │
              ▼                 ▼
       ┌────────────┐    ┌────────────┐
       │ Azure      │    │ Fallback   │
       │ OpenAI     │    │ generator  │
       │ (if enabled)│   │ (default)  │
       └─────┬──────┘    └─────┬──────┘
             │                 │
             └────────┬────────┘
                      │
                      ▼
             ┌───────────────────┐
             │  Delta table       │
             │  processed/        │
             │  summaries         │
             └───────────────────┘
```

### Two modes

| Mode | Trigger | Summary source |
|------|---------|----------------|
| Fallback | `AZURE_OPENAI_ENABLED=false` or unset | Deterministic generator |
| Azure OpenAI | `AZURE_OPENAI_ENABLED=true` and endpoint set | Deployed `gpt-4o-mini` |

The same pipeline code runs in both modes. Enabling Azure OpenAI requires only setting environment variables.

### Security

- **No API keys.** Authentication uses Microsoft Entra ID via `AzureCliCredential` locally and `DefaultAzureCredential` in Azure.
- The Databricks Managed Identity is granted `Cognitive Services OpenAI User` on the OpenAI account (via the `security` module, when the module is active).
- The connection is scoped to the specific OpenAI resource.

### Known limitation

Azure for Students subscriptions cannot provision Azure OpenAI due to quota restrictions. The Terraform module (`terraform/modules/ai/`) is preserved and validated but commented out in the environment wiring. The pipeline uses the deterministic fallback generator in the current environment.

The fallback is a Python template, not a model. It produces structured summaries from the same data, with a `is_fallback` flag and a disclaimer in the output.

See [ADR-004](docs/architecture/adr-004-ai-integration.md) for the full decision record, alternatives considered, and activation procedure.

### Documentation

See [Phase 7 — AI Integration](docs/phases/phase-7-ai.md) for the implementation record.

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
- The `Microsoft.Databricks` and `Microsoft.CognitiveServices` providers registered
- A storage account for the Terraform remote backend

**Known limitations (Azure for Students):**

- Databricks clusters cannot be provisioned (SKU restrictions). See [ADR-001](docs/architecture/adr-001-databricks-cluster-limitation.md).
- Azure OpenAI cannot be provisioned (quota restrictions). See [ADR-004](docs/architecture/adr-004-ai-integration.md).
- Azure DevOps pipelines cannot run on hosted agents (billing restrictions). See [Phase 4](docs/phases/phase-4-cicd.md).

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
│   │   ├── databricks/       # Workspace with VNet Injection
│   │   ├── monitoring/       # Application Insights, Log Analytics
│   │   ├── keyvault/         # Key Vault and Managed Identity
│   │   ├── security/         # Role assignments
│   │   └── ai/               # Azure OpenAI (preserved, not applied)
│   └── environments/
│       ├── dev/
│       ├── staging/
│       └── prod/
│
├── python/
│   ├── requirements.txt
│   ├── pytest.ini
│   ├── src/
│   │   ├── ai/               # AI integration (client, fallback, prompts, summarizer)
│   │   ├── api/              # BCB SGS client
│   │   ├── pipeline/         # ingest, validate, transform, persist
│   │   └── utils/            # logging, spark helpers, credentials
│   └── tests/                # unit and smoke tests
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
│   └── slos.md              # SLIs, SLOs, error budget policy
│
├── security/                 # RBAC and security-related Terraform (module)
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
    │   ├── phase-3-pipeline.md
    │   ├── phase-4-cicd.md
    │   ├── phase-5-observability.md
    │   ├── phase-6-security.md
    │   └── phase-7-ai.md
    ├── architecture/
    │   ├── README.md
    │   ├── security-model.md
    │   ├── adr-001-databricks-cluster-limitation.md
    │   ├── adr-002-observability-stack.md
    │   ├── adr-003-security-model.md
    │   └── adr-004-ai-integration.md
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
| Key Vault | `{env}-{project}-kv` | `dev-sredatabricks-kv` |
| Managed Identity | `{env}-{project}-{purpose}-mi` | `dev-sredatabricks-dbw-mi` |

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
| [Phase 5 — Observability](docs/phases/phase-5-observability.md) | SLIs/SLOs, metrics, dashboards, alerts |
| [Phase 6 — Security](docs/phases/phase-6-security.md) | Key Vault, RBAC, Managed Identities, cleanup |
| [Phase 7 — AI Integration](docs/phases/phase-7-ai.md) | Executive summaries with fallback strategy |
| [Security Model](docs/architecture/security-model.md) | Full security posture reference |
| [ADR-001](docs/architecture/adr-001-databricks-cluster-limitation.md) | Databricks cluster limitation |
| [ADR-002](docs/architecture/adr-002-observability-stack.md) | Observability stack selection |
| [ADR-003](docs/architecture/adr-003-security-model.md) | Security model decisions |
| [ADR-004](docs/architecture/adr-004-ai-integration.md) | AI integration strategy |
| [Operations](docs/operations/README.md) | Runbooks and procedures |
| [Troubleshooting](docs/troubleshooting/README.md) | Known issues and fixes |

---

## Cost Management

The project runs on a constrained budget. Controls in place:

- Databricks clusters with aggressive auto-termination (when provisionable)
- Only necessary resources kept active
- All resources can be destroyed with `make terraform-destroy`
- Data pipeline runs locally, avoiding compute costs in the cloud
- AI summaries use deterministic fallback (no token costs in current environment)
- Azure Cost Management for monitoring (planned for Phase 10)

---

## Manual Resources

Some resources were created manually in the Azure portal (Workbook, Action Group, Alert Rules, the Application Insights secret in Key Vault). They are documented in the [Post-apply checklist](docs/operations/README.md) and must be recreated after each `terraform destroy` + `terraform apply` cycle.

Migration to Terraform is planned for a later phase (see [ADR-002](docs/architecture/adr-002-observability-stack.md)).

---

## Roadmap

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 0** | Foundation: Git, Makefile, conventions | Completed |
| **Phase 1** | Base network: VNet, subnets, NSG | Completed |
| **Phase 2** | Databricks Workspace and Data Lake | Completed |
| **Phase 3** | Data pipeline with ingestion, validation, Delta | Completed |
| **Phase 4** | CI/CD with Azure DevOps | Completed |
| **Phase 5** | Observability: SLIs/SLOs, Application Insights, alerts | Completed |
| **Phase 6** | Security: Key Vault, RBAC, Managed Identities, cleanup | Completed |
| **Phase 7** | AI Integration: executive summaries with fallback strategy | Completed |
| **Phase 8** | AKS and containerized workloads | Next |
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
