# ADR-004 — AI Integration Strategy

**Status:** Accepted (with documented limitation)
**Date:** 2026-09-27
**Deciders:** Project author
**Context:** Phase 7 (AI Integration)

---

## Context and Problem Statement

Phase 7 aimed to integrate AI into the data pipeline to generate
executive summaries of Brazilian economic indicators in natural language.
Several architectural decisions were required:

1. Which AI use case to select
2. Which model and service to use
3. How to authenticate without long-lived secrets
4. What to do when the service cannot be provisioned
5. How to make the integration portable between enabled and disabled states

This ADR captures the reasoning behind each decision.

---

## Decision 1 — Executive summaries as the AI use case

### Problem

Five candidate use cases were evaluated:

| Case | Description |
|------|-------------|
| 1 | Executive summaries of economic indicators |
| 2 | Anomaly detection via LLM |
| 3 | Alert severity classification |
| 4 | Semantic enrichment of series |
| 5 | RAG over BCB documents (atas do COPOM) |

### Decision

**Case 1 — Executive summaries.**

### Rationale

- **Natural alignment with the pipeline output.** The pipeline already produces monthly aggregates per series. Generating a narrative summary of those aggregates is the next logical step.
- **High demonstrative value.** A reader can immediately see the value: instead of raw numbers, a concise narrative.
- **Low cost.** One call per pipeline execution. At `gpt-4o-mini` pricing, this is a fraction of a cent per run.
- **Testable.** The fallback can produce output with the same structure, so the pipeline can be validated end-to-end without the model.
- **Extensible.** Once the interface exists, adding other use cases (e.g., RAG) is additive.

### Alternatives rejected

| Case | Reason for rejection |
|------|---------------------|
| 2 | Statistical methods (Z-score, IQR, Isolation Forest) are more accurate and deterministic for anomaly detection. Using an LLM here is a solution looking for a problem. |
| 3 | The existing alert rules already classify severity (Error, Warning). An LLM would add latency and cost without improving the classification. |
| 4 | The project has 3 series. Semantic enrichment adds value in catalogs with dozens or hundreds of series. Artificial here. |
| 5 | RAG is valuable but significantly more complex (vector store, embeddings, ingestion pipeline). Deferred to a future phase. |

### Consequences

**Positive:**
- The pipeline gains a narrative layer aligned with its actual output
- The integration pattern (client, prompts, fallback) is reusable for future AI features
- Cost is negligible

**Negative:**
- In the current environment, summaries are template-based (see Decision 4)

---

## Decision 2 — Azure OpenAI with `gpt-4o-mini`

### Problem

Which AI service and model to use?

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Azure OpenAI with `gpt-4o-mini` | Managed, secure, Azure-native; requires quota |
| B | Azure OpenAI with `gpt-4o` | Higher quality; 10x cost |
| C | OpenAI public API | Simple, but requires external secret and outbound access |
| D | Local LLM (Ollama) | No cloud dependency; not Azure-focused |

### Decision

**Option A — Azure OpenAI with `gpt-4o-mini`.**

### Rationale

- **Azure-native.** The project's focus is Azure; using Azure OpenAI keeps the stack coherent.
- **Managed service.** No infrastructure to maintain; the service handles scaling, availability, and updates.
- **Secure authentication.** Supports Microsoft Entra ID authentication, avoiding API keys.
- **Cost-effective model.** `gpt-4o-mini` provides sufficient quality for structured summaries at a fraction of `gpt-4o` cost.
- **Enterprise-ready.** The same pattern (account, deployment, RBAC) is used in production Azure environments.

### Model choice

| Model | Quality | Cost (per 1M tokens) | Verdict |
|-------|---------|---------------------|---------|
| `gpt-4o-mini` | Sufficient for structured summaries | ~$0.15 input / $0.60 output | **Selected** |
| `gpt-4o` | Higher, but not needed | ~$2.50 input / $10.00 output | Rejected (cost) |
| `gpt-4-turbo` | Intermediate | ~$10 input / $30 output | Rejected (cost) |

### Deployment configuration

- **Deployment name:** `gpt-4o-mini`
- **Model version:** `2024-07-18`
- **SKU:** `GlobalStandard`
- **Capacity:** 10K TPM (tokens per minute)

`GlobalStandard` was chosen over `Standard` because it has better
availability for restricted subscriptions. 10K TPM is more than
sufficient for the project's volume (one call per pipeline execution).

### Consequences

**Positive:**
- Azure-native authentication via Microsoft Entra ID
- Zero API keys in code or configuration
- Pay-per-use; no provisioned throughput cost
- Model is enterprise-supported

**Negative:**
- Requires Azure OpenAI quota (see Decision 4)

---

## Decision 3 — Managed Identity authentication, no API keys

### Problem

How should the pipeline authenticate to the Azure OpenAI service?

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | API key stored in Key Vault | Simple, but reintroduces a secret |
| B | Managed Identity with `DefaultAzureCredential` | No secret; requires Azure context |
| C | Service Principal with client secret | No secret if using certificate; but still a credential |

### Decision

**Option B — Managed Identity with `DefaultAzureCredential` (and `AzureCliCredential` for local development).**

### Rationale

- **Consistent with Phase 6.** The project adopted zero long-lived secrets for service-to-service authentication. This decision extends that principle to AI.
- **Managed Identity is provisioned.** The `dev-sredatabricks-dbw-mi` identity was created in Phase 6. It is reused here.
- **The role assignment is explicit.** The Managed Identity has `Cognitive Services OpenAI User` on the OpenAI account (least privilege for inference).
- **Local development works.** `AzureCliCredential` (triggered by `AZURE_USE_CLI=true`) uses the operator's `az login` session.

### Token flow

```
   Pipeline (local)
        │
        │ AzureCliCredential
        ▼
   ┌──────────────────────┐
   │  Azure AD token      │
   │  (cognitiveservices) │
   └──────────┬───────────┘
              │
              │ Bearer token
              ▼
   ┌──────────────────────┐
   │  Azure OpenAI        │
   │  (inference)         │
   └──────────────────────┘


   Pipeline (Azure)
        │
        │ DefaultAzureCredential
        ▼
   ┌──────────────────────┐
   │  Managed Identity    │
   │  dev-sredatabricks   │
   │  -dbw-mi             │
   └──────────┬───────────┘
              │
              │ Bearer token
              ▼
   ┌──────────────────────┐
   │  Azure OpenAI        │
   │  (inference)         │
   └──────────────────────┘
```

### Consequences

**Positive:**
- No API keys stored or rotated
- Access is scoped to the specific OpenAI resource
- Auditable: the identity making the call is visible in logs

**Negative:**
- Requires the Managed Identity to be granted the correct role
- Local development depends on `az login`

---

## Decision 4 — Fallback strategy for quota-restricted environments

### Problem

During provisioning, the following error occurred:

```
InsufficientQuota: Insufficient quota. Cannot create/update/move
resource 'dev-sredatabricks-openai'.
```

Azure for Students subscriptions are categorized as restricted
subscription types. Microsoft does not allocate Azure OpenAI quota to
them by default.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Abandon the AI phase | No integration demonstrated |
| B | Upgrade to Pay-As-You-Go | Not available in the current context |
| C | Use a local LLM (Ollama) | Requires local setup; not Azure |
| D | Implement a deterministic fallback generator | Preserves pipeline, honest about limitation |
| E | Mock the model (return fixed string) | No demonstrable value |

### Decision

**Option D — Deterministic fallback generator.**

### Rationale

- **Preserves the pipeline.** The pipeline runs end-to-end regardless of whether the model is available.
- **Honest.** The fallback output clearly indicates it was not generated by AI.
- **Same interface.** The client, summarizer, and persist steps are identical in both modes.
- **No code changes to enable the model.** Only environment variables change.
- **The Terraform module is preserved.** It is validated and ready to apply when quota becomes available.

### How the fallback works

The fallback is a **Python template** that produces a structured
summary from the same data a model would use. It is not a model. It
does not understand language. It applies deterministic rules:

| Rule | Description |
|------|-------------|
| Trend detection | Compares first and last month's mean value; classifies as elevação, redução, or estabilidade |
| Statistics | Computes overall mean, min, and max per series |
| Narrative | Formats the results in fixed paragraphs |

The output follows the same schema as the AI-generated summary, so
downstream consumers do not need to distinguish.

### Consequences

**Positive:**
- The pipeline is functional in the current environment
- The architecture of the AI integration is demonstrated
- The ADR documents the limitation transparently

**Negative:**
- The fallback is not AI. It does not provide the linguistic flexibility of a model.
- In the current environment, "AI" is architectural, not operational.

**Mitigations:**
- The summary text explicitly states it was generated by a fallback
- The ADR documents activation steps for when quota becomes available
- The Terraform module is validated and ready to apply

### Alternatives rejected

- **Ollama local LLM:** Rejected because it introduces a new runtime
  component (Ollama server), requires ~5-8 GB of disk for the model,
  and shifts the project away from the Azure focus.
- **HuggingFace Inference API:** Rejected because it introduces an
  external secret (API token) and moves away from Azure-native
  authentication.
- **OpenAI public API:** Rejected for the same reasons, plus the need
  for an international credit card.

---

## Decision 5 — Interface abstraction for portability

### Problem

How to structure the code so that the same pipeline runs with and
without the model?

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | If-else in the pipeline directly | Simple but couples business logic to model availability |
| B | Abstract client with two implementations | More code, but clean separation |
| C | Separate pipelines for each mode | Duplication |

### Decision

**Option B — Abstract client with two implementations.**

### Rationale

- **Single responsibility.** The client decides how to invoke; the summarizer decides what to invoke with; the pipeline orchestrates.
- **Testable.** The fallback can be tested independently of the model.
- **Reusable.** The pattern can be extended to future AI features (e.g., RAG, classification).
- **Zero code change at activation.** Only environment variables change.

### Module structure

```
python/src/ai/
├── __init__.py
├── client.py       # Decides: model or fallback
├── fallback.py     # Deterministic implementation
├── prompts.py      # Prompt templates
└── summarizer.py   # Orchestrates: prompt building + client invocation
```

### Consequences

**Positive:**
- Clean separation of concerns
- Both modes tested by the same test suite
- The client is the only place that knows about the environment

**Negative:**
- Slightly more code than a simple if-else

---

## Alternatives Considered Overall

### Multi-provider abstraction

Supporting both Azure OpenAI and OpenAI public from the start was
considered. Rejected because:

- The project's scope is Azure-specific
- Adding a second provider without a use case is premature abstraction
- The client abstraction already supports adding providers later

### Serverless invocation (Azure Functions)

Invoking the model from an Azure Function triggered by the pipeline was
considered. Rejected because:

- Adds a new compute resource with its own cost and complexity
- The pipeline runs locally; a Function would be accessible only in Azure
- Not aligned with the current development workflow

---

## References

- [Phase 7 — AI Integration](../phases/phase-7-ai.md)
- [Security Model](security-model.md)
- [ADR-003 — Security Model Decisions](adr-003-security-model.md)
- Microsoft documentation: Azure OpenAI quotas and limits
- Microsoft documentation: Azure for Students subscription restrictions
- OpenAI Python SDK: `AzureOpenAI` client with `azure_ad_token`

---

## Revision History

| Date | Change |
|------|--------|
| 2026-09-27 | Initial decision recorded |
