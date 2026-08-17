# Convenções do Projeto

## Nomenclatura de Recursos Azure

| Tipo | Padrão | Exemplo |
|------|--------|---------|
| Resource Group | `{env}-{project}-{purpose}-rg` | `dev-sre-databricks-rg` |
| VNet | `{env}-{project}-vnet` | `dev-sre-databricks-vnet` |
| Subnet | `{env}-{project}-{type}-subnet` | `dev-sre-databricks-data-subnet` |
| Storage Account | `{env}{project}{purpose}sa` | `devsredatabricksdatasa` |
| Databricks Workspace | `{env}-{project}-dbw` | `dev-sre-databricks-dbw` |
| AKS Cluster | `{env}-{project}-aks` | `dev-sre-databricks-aks` |

## Branches Git

- `main` - Produção (protegida)
- `develop` - Integração (padrão)
- `feature/*` - Novas funcionalidades
- `hotfix/*` - Correções urgentes

## Tags e Releases

- `v{major}.{minor}.{patch}` - Versão semântica
- `v1.0.0`, `v1.1.0`, `v1.1.1`

## Variáveis de Ambiente

Todas as variáveis sensíveis devem ser armazenadas no arquivo `.env` (não versionado). O arquivo `.env.example` deve conter a estrutura esperada.

## Comandos Make

Todos os comandos de automação devem ser definidos no Makefile, com targets claros e documentados.

## Documentação

- README.md - Visão geral e setup inicial
- docs/architecture/ - Decisões arquiteturais (ADRs)
- docs/operations/ - Runbooks e procedimentos operacionais
- docs/troubleshooting/ - Guias de resolução de problemas
