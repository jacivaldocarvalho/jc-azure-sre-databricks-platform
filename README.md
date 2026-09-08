# Azure SRE/Databricks Platform

A hands-on project focused on **SRE and DevOps practices in Microsoft Azure**, with an emphasis on **Infrastructure as Code (IaC), Databricks, CI/CD, observability, security, and automation**.

## Core Technologies

* Azure Cloud
* Terraform (Infrastructure as Code)
* Azure DevOps (CI/CD)
* Databricks (Data Processing & ML)
* Kubernetes / AKS
* Python and Shell Scripting
* Prometheus and Grafana (Observability)

## Project Structure

```text
azure-sre-databricks-platform/
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

## Prerequisites

Before getting started, install:

* Git
* Terraform >= 1.5.0
* Azure CLI
* Python >= 3.9
* Databricks CLI
* kubectl
* Make

You also need access to an **Azure subscription** with sufficient permissions for the upcoming phases of the project.

## Initial Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd azure-sre-databricks-platform
```

### 2. Configure Environment Variables

Create your local environment file from the provided example:

```bash
cp .env.example .env
```

Edit the `.env` file and provide the credentials and configuration required for your local environment.

> **Important:** The `.env` file must not be committed to version control. Never add credentials, tokens, secrets, or private keys to the repository.

### 3. Authenticate with Azure

```bash
az login
az account set --subscription <subscription-id>
```

Confirm the selected subscription:

```bash
az account show
```

### 4. Initialize the Project

Run:

```bash
make init
```

This command prepares the local configuration required for development and creates the `.env` file if it does not already exist.

## Branching Strategy

The project uses the following branching model:

* `main` — stable, production-ready code
* `develop` — integration and development branch
* `feature/*` — development of new features
* `hotfix/*` — urgent fixes

Example:

```bash
git checkout develop
git checkout -b feature/feature-name
```

Changes should be developed in dedicated branches and merged into `develop` through Pull Requests.

## Useful Commands

| Command                  | Description                                                           |
| ------------------------ | --------------------------------------------------------------------- |
| `make help`              | Lists the available commands                                          |
| `make init`              | Initializes the local project configuration                           |
| `make validate`          | Validates the Terraform configuration for the development environment |
| `make format`            | Formats Terraform and Python files                                    |
| `make clean`             | Removes temporary files and local artifacts                           |
| `make terraform-init`    | Initializes Terraform in the `dev` environment                        |
| `make terraform-plan`    | Generates the Terraform execution plan for the `dev` environment      |
| `make terraform-apply`   | Applies infrastructure changes to the `dev` environment               |
| `make terraform-destroy` | Destroys Terraform-managed resources in the `dev` environment         |

> **Warning:** `terraform-apply` and `terraform-destroy` can modify or remove Azure resources. Always review the output of `terraform plan` before applying changes.

## Initial Validation

After completing the setup, validate the environment with:

```bash
make help
make validate
make format
```

To check the repository status:

```bash
git status
git branch
```

## Environments

The infrastructure is organized into separate environments:

```text
terraform/
└── environments/
    ├── dev/
    ├── staging/
    └── prod/
```

Each environment has its own Terraform configuration and will evolve independently throughout the different phases of the project.

## Security

The following practices should be maintained throughout development:

* Never commit the `.env` file
* Never store secrets directly in Terraform files
* Never commit tokens, passwords, or private keys
* Use secure secret management mechanisms as the platform evolves
* Review infrastructure changes before running `terraform apply`
* Follow the principle of least privilege for Azure permissions

## Documentation

Additional documentation is organized under `docs/`:

```text
docs/
├── architecture/       # Architecture and architectural decisions
├── operations/         # Runbooks and operational procedures
├── troubleshooting/    # Troubleshooting guides
└── conventions.md      # Project conventions
```

## Next Steps

After completing the initial setup, the planned next steps are:

1. Configure the Terraform remote backend
2. Provision the base network infrastructure (VNet and subnets)
3. Configure and deploy the Databricks Workspace
4. Implement data pipelines
5. Configure observability
6. Implement CI/CD
7. Enhance platform security and governance

## Project Status

The project is currently in **Phase 2 — Databricks Workspace and Integration**.

The goal of this phase is to provision the Databricks environment and establish its integration with data storage, preparing the infrastructure required for data development and processing.

* Provision the Databricks Workspace using Terraform
* Configure Azure Data Lake Storage (ADLS) for data storage
* Set up Unity Catalog and the metastore
* Create the initial development cluster

**Validation:** verify workspace access, confirm that the cluster is operational, and validate read and write operations against ADLS.

## License

MIT
