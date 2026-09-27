# Phase 7 — AI Integration

**Status:** Completed (with documented limitation)
**Duration:** Multi-iteration (case selection, Azure OpenAI provisioning attempt, fallback strategy, pipeline integration)
**Dependencies:** Phase 6 (Security)

---

## Objective

Integrate AI into the data pipeline to generate executive summaries of
Brazilian economic indicators in natural language. The result should:

- Add a demonstrable AI capability to the project
- Respect the security model established in Phase 6 (no long-lived secrets)
- Emit metrics aligned with the observability model from Phase 5
- Work in environments where Azure OpenAI is not provisionable

---

## Context

### Motivation

The pipeline produces structured aggregates (monthly means, min, max,
observation counts) but no narrative. A financial analyst reading the
dashboard must interpret the numbers manually. Generating a concise
executive summary in natural language adds tangible value to the output
and demonstrates an end-to-end AI integration.

### Case selection

Five candidate use cases were evaluated:

| Case | Description | Verdict |
|------|-------------|---------|
| 1 | Executive summaries of economic indicators | **Selected** |
| 2 | Anomaly detection via LLM | Rejected (statistical methods are superior) |
| 3 | Alert severity classification | Rejected (rules already cover this) |
| 4 | Semantic enrichment of series | Rejected (low value with 3 series) |
| 5 | RAG over BCB documents | Considered, deferred to a future phase |

Case 1 was selected because it has high demonstrative value, low cost,
and integrates directly with the existing pipeline output.

### Subscription constraint

The project runs on an **Azure for Students** subscription. During
provisioning of the Azure OpenAI resource, the following error was
observed:

```
InsufficientQuota: Insufficient quota. Cannot create/update/move
resource 'dev-sredatabricks-openai'.
```

Azure for Students subscriptions are categorized as **restricted
subscription types**. Microsoft does not allocate Azure OpenAI quota to
these subscriptions by default. This is a platform-level restriction,
not a configuration error.

See [ADR-004](../architecture/adr-004-ai-integration.md) for the full
decision record.

---

## Implementation

### 1. Terraform module (preserved, not applied)

Created `terraform/modules/ai/` with:

- `azurerm_cognitive_account` — Azure OpenAI account (kind OpenAI, SKU S0)
- `azurerm_cognitive_deployment` — deployment of `gpt-4o-mini` (GlobalStandard, 10K TPM)

The module is **validated** (`terraform validate` passes) and **ready to
apply**. In the current environment it is commented out in
`terraform/environments/dev/main.tf` to prevent the quota error during
`terraform apply`.

### 2. Security module update

Added `azurerm_role_assignment.databricks_openai_user` in
`terraform/modules/security/` to grant the Databricks Managed Identity
the `Cognitive Services OpenAI User` role on the OpenAI account.

The resource is conditional via `count = var.openai_account_id != "" ? 1 : 0`.
When the environment passes an empty string (current state), the resource
is not created.

### 3. Python AI module

Created `python/src/ai/` with:

| Module | Purpose |
|--------|---------|
| `client.py` | Abstraction over the AI model. Decides between Azure OpenAI and fallback. |
| `fallback.py` | Deterministic summary generator used when AI is not enabled. |
| `prompts.py` | System and user prompt templates, kept separate from code. |
| `summarizer.py` | Orchestrates the summary generation. |
| `__init__.py` | Package marker. |

Additionally, `python/src/utils/credentials.py` was created to centralize
Azure credential resolution (used by the AI client and available for
other modules).

### 4. Pipeline integration

`python/src/run_pipeline.py` was updated to add two steps:

- **Step 5b** — Generate executive summary after the monthly aggregation
- **Step 6b** — Persist the summary to Delta (`processed/summaries`)

The summary is persisted as a single-row Delta table with columns:

| Column | Type | Purpose |
|--------|------|---------|
| `text` | string | Generated summary |
| `model` | string | Model used (or "fallback") |
| `is_fallback` | boolean | True when fallback was used |
| `input_tokens` | long | Token count for input (0 in fallback) |
| `output_tokens` | long | Token count for output |
| `period_start` | string | Start of the period |
| `period_end` | string | End of the period |
| `generated_at` | timestamp | Timestamp of generation |

### 5. Configuration

`.env.example` was updated with a section for Azure OpenAI:

```bash
AZURE_OPENAI_ENABLED=false
# AZURE_OPENAI_ENDPOINT=https://<resource>.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
```

`python/requirements.txt` was updated with `openai==1.54.0`.

### 6. Fallback strategy

The `client.py` module decides at runtime between two modes:

```
                        Pipeline invokes AI client
                                    │
                                    ▼
                    ┌───────────────────────────────┐
                    │  AZURE_OPENAI_ENABLED=true?   │
                    └───────────────┬───────────────┘
                                    │
                         Yes ───────┴─────── No
                          │                    │
                          ▼                    ▼
                ┌──────────────────┐  ┌──────────────────┐
                │ Invoke Azure     │  │ Use fallback     │
                │ OpenAI via SDK   │  │ generator        │
                └──────────┬───────┘  └──────────┬───────┘
                           │                     │
                           └──────────┬──────────┘
                                      │
                                      ▼
                            ┌──────────────────┐
                            │ Persist summary  │
                            │ to Delta         │
                            └──────────────────┘
```

The same code runs in both modes. Enabling Azure OpenAI requires only
setting the environment variables.

---

## Validation

### Pipeline execution

The pipeline runs successfully and produces the summary. Log excerpt:

```
INFO | __main__ | === Step 5b: Generate executive summary ===
INFO | src.ai.summarizer | Azure OpenAI is not enabled. Using fallback generator.
INFO | src.ai.fallback | Generating fallback summary (Azure OpenAI not enabled).
INFO | __main__ | Summary generated: model=fallback, fallback=True,
                  input_tokens=0, output_tokens=155
INFO | __main__ | === Step 6: Persist processed ===
INFO | src.pipeline.persist | Wrote 1010 rows to ./spark-warehouse/processed/variations
INFO | src.pipeline.persist | Wrote 72 rows to ./spark-warehouse/processed/monthly_aggregates
INFO | __main__ | === Step 6b: Persist summary ===
INFO | src.pipeline.persist | Wrote 1 rows to ./spark-warehouse/processed/summaries
INFO | __main__ | Pipeline completed successfully.
INFO | __main__ | Total pipeline duration: 22.80 seconds
```

### Generated summary (fallback mode)

```
Resumo executivo dos indicadores econômicos brasileiros no período de
janeiro de 2024 a dezembro de 2025. Foram analisadas as séries: SELIC, CDI, IPCA.

SELIC: iniciou o período em 0.0437 e encerrou em 0.0551 (elevação).
A média do período foi 0.0470, com mínima de 0.0393 e máxima de 0.0551.
Foram analisados 24 meses de dados.

CDI: iniciou o período em 0.0437 e encerrou em 0.0551 (elevação).
A média do período foi 0.0470, com mínima de 0.0393 e máxima de 0.0551.
Foram analisados 24 meses de dados.

IPCA: iniciou o período em 0.4200 e encerrou em 0.3300 (redução).
A média do período foi 0.3717, com mínima de -0.1100 e máxima de 1.3100.
Foram analisados 24 meses de dados.

Este resumo foi gerado por um gerador determinístico, pois o serviço de
Azure OpenAI não está habilitado no ambiente atual. Quando o serviço
estiver disponível, o resumo será gerado por um modelo de linguagem com
análise contextual mais rica.
```

### Query to verify the Delta table

```bash
python -c "
from src.utils.spark import get_spark_session
spark = get_spark_session()
df = spark.read.format('delta').load('./spark-warehouse/processed/summaries')
df.select('model', 'is_fallback', 'output_tokens', 'text').show(truncate=False)
spark.stop()
"
```

### Local checks

| Check | Result |
|-------|--------|
| `ruff check src/ tests/` | All checks passed |
| `pytest tests/ -v` | 10 passed |
| `terraform validate` | Success |
| `terraform plan` | No changes to infrastructure |

---

## Lessons Learned

### What worked well

- **Case selection before implementation:** evaluating five candidate
  use cases avoided adding AI without purpose. The selected case (executive
  summaries) is naturally aligned with the pipeline output.
- **Fallback strategy:** decoupling the AI invocation from the pipeline
  means the same code runs in both modes. Enabling Azure OpenAI in the
  future requires no code changes.
- **Centralized credential resolution:** moving the credential logic to
  `utils/credentials.py` makes it reusable and keeps `metrics.py` focused.
- **Prompt separation:** keeping prompts in `prompts.py` makes them easy
  to iterate on without touching code.

### Adjustments made

1. **Azure for Students quota limitation:** discovered during provisioning.
   Worked around by keeping the Terraform module in the codebase but
   commented out in the environment wiring, and by adding a fallback
   generator.

2. **Terraform `count` resolution:** the initial attempt to make the role
   assignment conditional used `module.ai.account_id` which is unknown
   during the first plan. Fixed by passing an empty string explicitly
   when the module is disabled, and adding `count` back to the resource.

3. **Provider version syntax:** the `azurerm_cognitive_deployment` resource
   uses `scale { type = "..." }` in provider 3.x. Provider 4.x uses
   `sku { name = "..." }`. This is documented for future upgrade.

4. **Language consistency:** the initial fallback used `strftime('%B')`
   which produced English month names. Fixed with a Portuguese month
   dictionary to keep the summary consistent.

### What would be done differently

- **Check quota availability before writing the module.** A quick
  verification of Azure OpenAI quota on the subscription would have
  surfaced the limitation earlier. This is the same lesson as Phase 4
  (billing eligibility).

---

## Artifacts

### Code

| Artifact | Path | Purpose |
|----------|------|---------|
| Terraform AI module | `terraform/modules/ai/` | Azure OpenAI account and deployment |
| Security role assignment | `terraform/modules/security/main.tf` | Managed Identity access |
| AI client | `python/src/ai/client.py` | Abstraction over Azure OpenAI / fallback |
| Fallback generator | `python/src/ai/fallback.py` | Deterministic summary |
| Prompts | `python/src/ai/prompts.py` | Prompt templates |
| Summarizer | `python/src/ai/summarizer.py` | Orchestration |
| Credentials helper | `python/src/utils/credentials.py` | Centralized credential resolution |
| Pipeline integration | `python/src/run_pipeline.py` | Steps 5b and 6b |

### Delta tables

| Table | Rows | Purpose |
|-------|------|---------|
| `processed/summaries` | 1 per run | Generated executive summary |

### ADRs

- [ADR-004 — AI Integration Strategy](../architecture/adr-004-ai-integration.md)

---

## Activation Procedure

When Azure OpenAI becomes available:

1. Uncomment the `ai` module in `terraform/environments/dev/main.tf`
2. Uncomment the AI outputs
3. Change `openai_account_id = ""` to `openai_account_id = module.ai.account_id` in the security module
4. Run `terraform apply`
5. Set `AZURE_OPENAI_ENABLED=true` in `.env`
6. Set `AZURE_OPENAI_ENDPOINT` and `AZURE_OPENAI_DEPLOYMENT`
7. Run the pipeline; Azure OpenAI will be used automatically

No code changes are required.

---

## Next Phase

[Phase 8 — AKS](../phases/phase-8-aks.md): provision an AKS cluster
and deploy containerized workloads for the platform.
