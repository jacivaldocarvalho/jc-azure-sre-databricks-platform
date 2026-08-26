# Azure SRE/Databricks Platform

Projeto voltado à prática de SRE/DevOps em ambiente Azure, com foco em infraestrutura como código, Databricks, CI/CD, observabilidade, segurança e automação.

## Tecnologias Principais

* Azure Cloud
* Terraform (Infrastructure as Code)
* Azure DevOps (CI/CD)
* Databricks (Data Processing & ML)
* Kubernetes / AKS
* Python e Shell Scripting
* Prometheus e Grafana (Observabilidade)

## Estrutura do Projeto

```text
azure-sre-databricks-platform/
├── terraform/          # Infrastructure as Code
├── azure-devops/       # CI/CD Pipelines
├── databricks/         # Notebooks e Jobs
├── monitoring/         # Observabilidade
├── security/           # RBAC e Políticas
├── kubernetes/         # Manifests AKS
├── python/             # Código Python
├── scripts/             # Automações
└── docs/               # Documentação
```

## Pré-requisitos

Antes de iniciar, instale:

* Git
* Terraform >= 1.5.0
* Azure CLI
* Python >= 3.9
* Databricks CLI
* kubectl
* Make

Também é necessário ter acesso a uma assinatura Azure com permissões suficientes para as próximas fases do projeto.

## Configuração Inicial

### 1. Clonar o repositório

```bash
git clone <repository-url>
cd azure-sre-databricks-platform
```

### 2. Configurar as variáveis de ambiente

Crie o arquivo local de variáveis a partir do exemplo:

```bash
cp .env.example .env
```

Edite o arquivo `.env` e preencha as credenciais e configurações necessárias para o ambiente local.

> **Importante:** o arquivo `.env` não deve ser versionado. Nunca adicione credenciais, tokens, secrets ou chaves privadas ao repositório.

### 3. Autenticar na Azure

```bash
az login
az account set --subscription <subscription-id>
```

Confirme a assinatura selecionada:

```bash
az account show
```

### 4. Inicializar o projeto

Execute:

```bash
make init
```

O comando prepara a configuração local necessária para o desenvolvimento e cria o arquivo `.env` caso ele ainda não exista.

## Fluxo de Branches

O projeto utiliza o seguinte modelo:

* `main` — código estável e pronto para produção
* `develop` — branch de integração e desenvolvimento
* `feature/*` — desenvolvimento de novas funcionalidades
* `hotfix/*` — correções urgentes

Exemplo:

```bash
git checkout develop
git checkout -b feature/nome-da-feature
```

Alterações devem ser desenvolvidas em branches específicas e integradas à `develop` por meio de Pull Requests.

## Comandos Úteis

| Comando                  | Descrição                                                        |
| ------------------------ | ---------------------------------------------------------------- |
| `make help`              | Lista os comandos disponíveis                                    |
| `make init`              | Inicializa a configuração local do projeto                       |
| `make validate`          | Valida as configurações Terraform do ambiente de desenvolvimento |
| `make format`            | Formata arquivos Terraform e Python                              |
| `make clean`             | Remove arquivos temporários e artefatos locais                   |
| `make terraform-init`    | Inicializa o Terraform no ambiente `dev`                         |
| `make terraform-plan`    | Gera o plano de alterações no ambiente `dev`                     |
| `make terraform-apply`   | Aplica as alterações no ambiente `dev`                           |
| `make terraform-destroy` | Destrói os recursos gerenciados pelo Terraform no ambiente `dev` |

> **Atenção:** `terraform-apply` e `terraform-destroy` podem alterar ou remover recursos Azure. Revise sempre o resultado do `terraform plan` antes de aplicar alterações.

## Validação Inicial

Após a configuração, valide o ambiente com:

```bash
make help
make validate
make format
```

Para verificar o estado do repositório:

```bash
git status
git branch
```

## Ambientes

A infraestrutura será organizada por ambientes:

```text
terraform/
└── environments/
    ├── dev/
    ├── staging/
    └── prod/
```

Cada ambiente possui sua própria configuração Terraform e será evoluído de forma independente ao longo das fases do projeto.

## Segurança

As seguintes práticas devem ser mantidas durante o desenvolvimento:

* Nunca versionar o arquivo `.env`
* Nunca armazenar secrets diretamente em arquivos Terraform
* Nunca versionar tokens, passwords ou chaves privadas
* Utilizar mecanismos seguros de gerenciamento de secrets conforme a evolução da plataforma
* Revisar alterações de infraestrutura antes de executar `terraform apply`
* Manter o princípio de menor privilégio nas permissões Azure

## Documentação

A documentação complementar está organizada em `docs/`:

```text
docs/
├── architecture/       # Arquitetura e decisões arquiteturais
├── operations/         # Runbooks e procedimentos operacionais
├── troubleshooting/    # Guias de troubleshooting
└── conventions.md      # Convenções do projeto
```

## Próximos Passos

Após a conclusão da configuração inicial, as próximas etapas previstas são:

1. Configuração do backend remoto do Terraform
2. Provisionamento da rede base (VNet e subnets)
3. Configuração e deploy do Databricks Workspace
4. Implementação dos pipelines de dados
5. Configuração de observabilidade
6. Implementação de CI/CD
7. Evolução da segurança e governança da plataforma


## Status do Projeto

O projeto está atualmente na Fase 2 — **Databricks Workspace e Integração**.

Esta fase tem como objetivo provisionar o ambiente Databricks e estabelecer sua integração com o armazenamento de dados, preparando a infraestrutura necessária para desenvolvimento e processamento de dados.

- Provisionar o Databricks Workspace via Terraform
- Configurar o Azure Data Lake Storage (ADLS) para armazenamento de dados
- Estabelecer o Unity Catalog e o metastore
- Criar o cluster inicial para desenvolvimento

**Validação**: acesso ao workspace, cluster operacional e validação de leitura e escrita no ADLS.

## Licença

MIT
