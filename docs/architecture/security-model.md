# Security Model

Reference document for the security posture of the JC-Azure SRE Databricks Platform.

---

## Purpose

This document describes **what** is protected, **from whom**, and **how**. It is intended to be:

- A reference for anyone operating the project
- A checklist for future phases that add new resources
- Evidence of a deliberate security posture for portfolio review

The document is updated whenever a new identity, secret, or access pattern is introduced.

---

## 1. Asset Inventory

### Data

| Asset | Location | Sensitivity | Protection |
|-------|----------|-------------|------------|
| Raw economic series | ADLS Gen2 container `raw` | Public data (BCB) | TLS, HNS, private access |
| Processed aggregates | ADLS Gen2 container `processed` | Public data (derived) | TLS, HNS, private access |
| Notebooks | ADLS Gen2 container `notebooks` | Source code | TLS, HNS, private access |
| Streaming checkpoints | ADLS Gen2 container `checkpoints` | Operational state | TLS, HNS, private access |
| Terraform state | Storage Account `tfstatejcsredatabricks` | Configuration | TLS, restricted access |

### Secrets

| Secret | Storage | Rotation |
|--------|---------|----------|
| Application Insights connection string | Azure Key Vault | On Application Insights recreation |
| Azure DevOps client credentials | Not stored (OIDC) | N/A |
| Azure CLI session tokens | Azure CLI cache (local) | Per `az login` |
| Azure OpenAI access | Not stored (Managed Identity / Azure CLI) | N/A |

**Note:** the project does not store any API keys, including for AI services. Authentication to Azure OpenAI is done via Microsoft Entra ID (Managed Identity in Azure, Azure CLI locally). See [ADR-004](adr-004-ai-integration.md).

### Compute

| Resource | Purpose | Access |
|--------|---------|--------|
| Databricks Workspace | Data processing and notebooks | VNet Injection, SCC |
| Local developer machine | Pipeline execution | Azure CLI session |
| Azure DevOps hosted agents | CI/CD (future) | OIDC + Service Connection |

---

## 2. Threat Model

A simplified threat model focused on realistic risks for this project.

### Actors

| Actor | Intent | Capability |
|-------|--------|------------|
| External attacker | Steal data or abuse resources | Limited to internet-facing surface |
| Compromised developer machine | Escalate to Azure resources | Access to local `.env` and CLI cache |
| Compromised CI/CD | Modify infrastructure or exfiltrate secrets | Access to Service Connection |
| Insider with read access | Understand the project | Reader-level permissions |

### Threats and Mitigations

| Threat | Likelihood | Impact | Mitigation |
|--------|-----------|--------|------------|
| Connection string leaked in Git | Low | Medium | `.gitignore`, Key Vault, no secrets in repo |
| Stolen Azure CLI token | Low | Medium | Tokens are short-lived; `az logout` revokes |
| Compromised Service Principal | Low | High | Reduced scope, OIDC instead of secrets |
| Orphaned credentials | Medium | High | Removed in Phase 6; periodic audits |
| Unauthorized access to ADLS | Low | High | Managed Identity, RBAC, private network |
| Denial of service via resource abuse | Low | Medium | Cost alerts (planned), least privilege |
| Prompt injection in AI summary | Low | Low | Input is structured data from BCB; no user-supplied prompts |
| Abuse of Azure OpenAI quota | Low | Medium | Scoped identity, low TPM deployment, cost monitoring |

### Out of Scope

- Advanced Persistent Threats (APT) — outside the project's realistic threat landscape
- Supply chain attacks on dependencies — managed by version pinning in `requirements.txt`
- Physical attacks on Azure datacenters — handled by Microsoft

---

## 3. Identity Inventory

### Human Identities

| Identity | Purpose | Roles |
|----------|---------|-------|
| Owner (project author) | Development and operations | Key Vault Administrator (on the project Key Vault) |

### Service Identities

| Identity | Type | Purpose | Roles |
|----------|------|---------|-------|
| `jc-sre-databricks-pipeline` | App Registration (Service Principal) | Azure DevOps pipelines | Contributor (at Resource Group scope) |
| `dev-sredatabricks-dbw-mi` | User-Assigned Managed Identity | Databricks workspace and pipeline | Key Vault Secrets User, Storage Blob Data Contributor, Cognitive Services OpenAI User (conditional) |
| Azure DevOps OIDC | Federated Credential | Pipeline authentication | Federated to `jc-sre-databricks-pipeline` |

**Note:** the `Cognitive Services OpenAI User` role is conditional on the Azure OpenAI resource being provisioned. In the current environment (Azure for Students), the AI module is commented out and the role is not assigned. See [ADR-004](adr-004-ai-integration.md).

### Removed Identities

| Identity | Removed in | Reason |
|----------|------------|--------|
| Legacy Service Principal `58ce9313-...` | Phase 6 | Replaced by OIDC; orphaned credential |

---

## 4. Role Assignments

### By Scope

#### Subscription

```
┌─────────────────────────────────────────────────────────┐
│  Subscription: Azure for Students                       │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Role: Owner                                            │
│  Principal: Project author                              │
│  Purpose: Provisioning, administrative operations       │
│                                                         │
│  Role: (none for Service Principals)                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Resource Group `dev-sredatabricks-rg`

```
┌─────────────────────────────────────────────────────────┐
│  Resource Group: dev-sredatabricks-rg                   │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Role: Contributor                                      │
│  Principal: jc-sre-databricks-pipeline (Azure DevOps)   │
│  Purpose: Manage all resources in the RG from CI/CD     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Data Lake Storage Account

```
┌─────────────────────────────────────────────────────────┐
│  Storage: devsredata (ADLS Gen2)                        │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Role: Storage Blob Data Contributor                    │
│  Principal: dev-sredatabricks-dbw-mi                    │
│  Purpose: Read/write containers (raw, processed, etc.)  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Key Vault

```
┌─────────────────────────────────────────────────────────┐
│  Key Vault: dev-sredatabricks-kv                        │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Role: Key Vault Administrator                          │
│  Principal: Project author                              │
│  Purpose: Manage secrets manually                       │
│                                                         │
│  Role: Key Vault Secrets User                           │
│  Principal: dev-sredatabricks-dbw-mi                    │
│  Purpose: Read secrets from Databricks                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### Azure OpenAI (conditional)

```
┌─────────────────────────────────────────────────────────┐
│  Azure OpenAI: dev-sredatabricks-openai                 │
│  ─────────────────────────────────────────────────────  │
│                                                         │
│  Status: Not provisioned in the current environment     │
│  Reason: Azure for Students quota restriction           │
│                                                         │
│  Role (when provisioned): Cognitive Services OpenAI User│
│  Principal: dev-sredatabricks-dbw-mi                    │
│  Purpose: Invoke the deployed gpt-4o-mini model         │
│                                                         │
│  See ADR-004 for the full decision record.              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5. Authentication Flows

### Flow 1: Local development

```
   Developer machine
        │
        │  az login
        ▼
   ┌──────────────────────┐
   │  Azure CLI cache     │
   │  (~/.azure/)         │
   └──────────┬───────────┘
              │
              │  Tokens (short-lived)
              │
              ▼
   ┌──────────────────────┐         ┌──────────────────────┐
   │  Terraform           │────────▶│  Azure Resource      │
   │  (uses az login)     │         │  Manager             │
   └──────────────────────┘         └──────────────────────┘
   ┌──────────────────────┐         ┌──────────────────────┐
   │  Python pipeline     │────────▶│  Key Vault           │
   │  (AzureCliCredential)│         │  (read secrets)      │
   └──────────────────────┘         └──────────────────────┘
```

**Characteristic:** no long-lived secrets. Tokens are cached locally in the Azure CLI session and expire based on tenant policy.

### Flow 2: Azure DevOps CI/CD

```
   Developer push
        │
        ▼
   ┌──────────────────────┐
   │  Azure DevOps        │
   │  Pipeline run        │
   └──────────┬───────────┘
              │
              │  Requests OIDC token
              │
              ▼
   ┌──────────────────────┐         ┌──────────────────────┐
   │  Microsoft Entra     │◀────────│  Federated Credential│
   │  (issuer validation) │         │  (in App Reg)        │
   └──────────┬───────────┘         └──────────────────────┘
              │
              │  Short-lived token
              │
              ▼
   ┌──────────────────────┐         ┌──────────────────────┐
   │  Service Principal   │────────▶│  Azure Resource      │
   │  (Contributor at RG) │         │  Manager             │
   └──────────────────────┘         └──────────────────────┘
```

**Characteristic:** no client secret. The token is issued per pipeline run and validated against the Federated Credential.

### Flow 3: Databricks runtime

```
   Databricks Workspace
        │
        │  Uses Managed Identity
        ▼
   ┌──────────────────────┐
   │  dev-sredatabricks   │
   │  -dbw-mi             │
   └──────────┬───────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
   ┌────────┐   ┌──────────┐
   │ Key    │   │ ADLS     │
   │ Vault  │   │ Gen2     │
   │ (read) │   │ (read/w) │
   └────────┘   └──────────┘
```

**Characteristic:** no credentials in code or configuration. The identity is assigned to the workspace and used transparently.

### Flow 4: Python pipeline — secret resolution

```
   Pipeline starts
        │
        ▼
   ┌─────────────────────────────┐
   │  AZURE_USE_CLI=true?        │
   └─────────┬───────────────────┘
             │
      Yes ───┴─── No
       │           │
       ▼           ▼
   ┌────────┐ ┌──────────────────┐
   │AzureCli│ │ DefaultAzure     │
   │Cred    │ │ Credential       │
   └───┬────┘ └────────┬─────────┘
       │               │
       └───────┬───────┘
               │
               ▼
   ┌─────────────────────────────┐
   │  Env var                    │
   │  APPLICATIONINSIGHTS_...   │
   │  set?                       │
   └─────────┬───────────────────┘
             │
      Yes ───┴─── No
       │           │
       ▼           ▼
   ┌────────┐ ┌──────────────────┐
   │Use env │ │ Read from        │
   │var     │ │ Key Vault        │
   └────────┘ └──────────────────┘
```

**Characteristic:** explicit priority order; no fallback ambiguity.

### Flow 5: AI invocation

```
   Pipeline reaches Step 5b
        │
        ▼
   ┌─────────────────────────────────┐
   │  AZURE_OPENAI_ENABLED=true?     │
   └─────────────┬───────────────────┘
                 │
          Yes ───┴─── No
           │           │
           ▼           ▼
   ┌────────────┐ ┌──────────────┐
   │  Azure     │ │  Fallback    │
   │  OpenAI    │ │  generator   │
   │  via       │ │  (template)  │
   │  Entra ID  │ │              │
   └─────┬──────┘ └──────┬───────┘
         │               │
         └───────┬───────┘
                 │
                 ▼
   ┌─────────────────────────────┐
   │  Persist summary to Delta   │
   │  processed/summaries        │
   │  (is_fallback column)       │
   └─────────────────────────────┘
```

**Characteristic:** the pipeline always produces a summary. The source (model or fallback) is transparent to downstream consumers, but is explicitly recorded in the `is_fallback` column.

---

## 6. Least Privilege by Design

The following principles are applied consistently:

### 1. Scope minimization

| Identity | Minimum scope needed | Scope granted |
|----------|---------------------|---------------|
| Azure DevOps SP | Manage resources in the project RG | Resource Group |
| Databricks MI | Read/write to ADLS containers | Storage Account |
| Databricks MI | Read Application Insights secret | Key Vault |
| Databricks MI | Invoke Azure OpenAI models | OpenAI account (conditional) |

### 2. No shared secrets

- Storage access is via Managed Identity, not account keys
- CI/CD is via OIDC, not client secrets
- Local development is via Azure CLI, not stored credentials
- AI invocation uses Microsoft Entra ID, not API keys

### 3. No secrets in code or config files

- `.env` is in `.gitignore`
- `.env.example` contains only placeholders
- Secrets live in Key Vault, not in Terraform state (where possible)

### 4. Explicit credential selection

- `AZURE_USE_CLI=true` in local development avoids ambiguous fallbacks
- `DefaultAzureCredential` is used only in environments where the chain is deterministic

### 5. Periodic audits

Documented in `docs/operations/README.md`:

- Review role assignments quarterly
- Revoke unused credentials
- Confirm no unexpected identities have access

---

## 7. Secret Lifecycle

| Stage | Action | Owner |
|-------|--------|-------|
| Creation | Generate in source system (Azure portal, CLI) | Operator |
| Storage | Store in Key Vault immediately | Operator |
| Distribution | Never distribute; consumers read from Key Vault | N/A |
| Use | Retrieved at runtime via Managed Identity or Azure CLI | Runtime |
| Rotation | On source system change or quarterly | Operator |
| Revocation | Delete in source and Key Vault | Operator |

Secrets that are not used should be revoked immediately. This was applied in Phase 6 when the legacy Service Principal secret was revoked.

---

## 8. Auditing and Monitoring

### What is logged

| Source | Content | Retention |
|--------|---------|-----------|
| Azure Activity Log | Resource operations | 90 days (default) |
| Key Vault diagnostic logs (future) | Secret access | Not enabled yet |
| Application Insights | Pipeline metrics | 90 days (default) |
| Azure DevOps pipeline logs | CI/CD runs | Per organization policy |

### Planned improvements

- Enable Key Vault diagnostic logs to Log Analytics (Phase 10)
- Enable Defender for Cloud recommendations review (Phase 10)
- Periodic review of role assignments (documented in operations runbook)

---

## 9. Compliance Considerations

The project is not subject to formal compliance frameworks. However, the practices adopted are aligned with:

| Framework | Relevant Practices Applied |
|-----------|---------------------------|
| CIS Azure Foundations | Key Vault RBAC, least privilege, no public blob access |
| Microsoft Cloud Adoption Framework | Identity-first, secrets in Key Vault |
| Zero Trust principles | Verify explicitly, least privilege, assume breach |

---

## 10. Known Limitations

| Limitation | Impact | Planned Resolution |
|------------|--------|-------------------|
| Key Vault has public network access | Secret access is from internet | Private Endpoint in future phase |
| No Key Vault diagnostic logs | Secret access not audited | Enable in Phase 10 |
| No conditional access policies | No location or device restrictions | Out of scope for student subscription |
| No Defender for Cloud | No continuous security recommendations | Enable in Phase 10 |
| Azure OpenAI not provisioned | AI summaries use deterministic fallback | Requires Pay-As-You-Go subscription (see [ADR-004](adr-004-ai-integration.md)) |

---

## 11. Related Documents

- [Phase 6 — Security](../phases/phase-6-security.md) — full implementation record for security
- [Phase 7 — AI Integration](../phases/phase-7-ai.md) — full implementation record for AI
- [ADR-003 — Security Model Decisions](adr-003-security-model.md) — security architectural decisions
- [ADR-004 — AI Integration Strategy](adr-004-ai-integration.md) — AI decisions and activation procedure
- [Operations](../operations/README.md) — day-to-day procedures and post-apply checklist
- [Troubleshooting](../troubleshooting/README.md) — common issues and fixes

---

## Revision History

| Date | Change |
|------|--------|
| 2026-09-26 | Initial security model documented after Phase 6 |
| 2026-09-27 | Added AI-related entries (OpenAI role assignment, threat model, authentication flow) |
