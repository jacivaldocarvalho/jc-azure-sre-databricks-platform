# ADR-003 — Security Model Decisions

**Status:** Accepted
**Date:** 2026-09-26
**Deciders:** Project author
**Context:** Phase 6 (Security)

---

## Context and Problem Statement

Phase 6 required the project to adopt a coherent security posture covering secrets management, identity, and access control. Several architectural decisions had to be made. This ADR captures them.

The decisions address four questions:

1. Where should secrets be stored?
2. How should the pipeline authenticate locally and in Azure?
3. What scope should the CI/CD Service Principal have?
4. How should the Databricks workspace access the Data Lake?

---

## Decision 1 — Key Vault as the central secrets store

### Problem

Before Phase 6, the Application Insights connection string was stored in a `.env` file on the developer machine. This worked for local development but had several issues:

- Secrets could leak if `.env` were accidentally committed or copied
- No central place to manage or rotate secrets
- No audit trail of secret access

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Keep secrets in `.env` only | Simplest; no central management |
| B | Azure Key Vault with access policies | Central storage; legacy authorization model |
| C | Azure Key Vault with RBAC authorization | Central storage; integrates with role assignments |

### Decision

**Option C — Azure Key Vault with RBAC authorization.**

### Rationale

- RBAC-based access integrates with the same role assignment model used elsewhere in the project
- Managed Identities can be granted access with the same `azurerm_role_assignment` pattern
- No separate "access policy" configuration to maintain
- Aligned with Microsoft's recommendation for new deployments

### Consequences

**Positive:**
- Secrets are centralized and can be rotated in one place
- Access is auditable via role assignments
- Local development can still use `.env` for debugging, with a documented precedence order

**Negative:**
- Additional infrastructure to provision and maintain
- Requires authentication to read secrets, which adds a step in local development

### Mitigations

- `AZURE_USE_CLI=true` forces `AzureCliCredential` locally, avoiding credential ambiguity
- The `.env` precedence allows debugging without Key Vault access when needed
- Key Vault is part of the standard `terraform apply`, so no extra manual step

---

## Decision 2 — Managed Identity for Databricks, not shared account keys

### Problem

The Databricks workspace needs to read and write to the Data Lake Storage Gen2. There are multiple ways to authorize this.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Use storage account keys in the Databricks cluster configuration | Simple; keys grant full access; keys must be rotated |
| B | Use a Service Principal with a client secret | Scoped; but requires managing a secret |
| C | Use a User-Assigned Managed Identity | Scoped; no secret; auditable |

### Decision

**Option C — User-Assigned Managed Identity** (`dev-sredatabricks-dbw-mi`).

### Rationale

- No secret to manage or rotate
- Access is scoped to specific containers via RBAC
- Activity is auditable at the identity level
- Reusable across multiple workspaces or services if needed
- Aligned with zero-trust principles

### Consequences

**Positive:**
- No account keys in configuration or notebooks
- Access can be revoked by removing the role assignment
- Consistent with the project's other authentication flows (OIDC for CI/CD, Azure CLI for local)

**Negative:**
- The Databricks workspace must be configured to use the Managed Identity for accessing ADLS (cluster-level configuration)
- Requires the workspace to support User-Assigned Managed Identities (premium tier, already provisioned)

### Grants applied

| Identity | Role | Scope |
|----------|------|-------|
| `dev-sredatabricks-dbw-mi` | Storage Blob Data Contributor | Storage Account `devsredata` |
| `dev-sredatabricks-dbw-mi` | Key Vault Secrets User | Key Vault `dev-sredatabricks-kv` |

---

## Decision 3 — Reduce Azure DevOps Service Principal scope

### Problem

The Azure DevOps Service Principal created in Phase 4 had `Contributor` at the **subscription** scope. This was necessary during initial setup but was broader than needed for ongoing operation.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Keep Contributor at subscription scope | Simple; enables creating new Resource Groups; larger blast radius |
| B | Reduce to Contributor at the project Resource Group | Least privilege; cannot create new Resource Groups |
| C | Replace with custom role limited to specific resource types | Very tight control; more maintenance; requires defining the role |

### Decision

**Option B — Contributor at the Resource Group scope.**

### Rationale

- The project operates in a single Resource Group (`dev-sredatabricks-rg`)
- The Service Principal does not need to create additional Resource Groups
- Reduced blast radius if the Service Principal is compromised
- Aligns with the principle of least privilege

### Consequences

**Positive:**
- Compromising the CI/CD Service Principal does not grant access to other resources in the subscription
- Consistent with the security posture of the rest of the project

**Negative:**
- The pipeline can no longer create new Resource Groups
- If a future phase needs a new Resource Group (e.g., `staging`), the assignment must be extended

### Mitigations

- Documented in `docs/operations/README.md` as a known limitation
- The trade-off is accepted because the project uses a single Resource Group
- If needed, the assignment can be extended to a specific additional Resource Group without reverting to subscription scope

---

## Decision 4 — Explicit credential selection in local development

### Problem

`DefaultAzureCredential` tries multiple credential sources in a fixed order. In local development, this caused a security incident: the `.env` file still contained `AZURE_CLIENT_ID` and `AZURE_CLIENT_SECRET` for a legacy Service Principal. `DefaultAzureCredential` picked up those credentials before reaching `AzureCliCredential`, resulting in the wrong identity being used.

### Options

| Option | Description | Trade-offs |
|--------|-------------|------------|
| A | Continue using `DefaultAzureCredential` everywhere | Simpler code; ambiguous behavior with legacy env vars |
| B | Force `AzureCliCredential` in local development via an env flag | Predictable locally; `DefaultAzureCredential` in Azure |
| C | Use separate code paths for local and Azure | Explicit; more code to maintain |

### Decision

**Option B — Controlled by `AZURE_USE_CLI`.**

### Rationale

- Local development requires predictability: the operator knows which identity will be used
- Azure deployments benefit from `DefaultAzureCredential` (Managed Identity support, no CLI dependency)
- A single environment variable controls the behavior without duplicating code
- Explicit and auditable

### Consequences

**Positive:**
- Local runs always use the Azure CLI session, which the operator controls
- No more accidental authentication as a legacy Service Principal
- Documented in the `.env.example` and in `metrics.py`

**Negative:**
- One more environment variable to configure
- Developers must know about the pattern

### Mitigations

- `.env.example` documents the variable and its purpose
- The default behavior (`DefaultAzureCredential`) is safe for Azure deployments
- The pattern is explained in the code docstring

---

## Decision 5 — Remove the legacy Service Principal

### Problem

A Service Principal (`58ce9313-...`) from Phase 1 had:
- `Contributor` at the subscription scope
- An active client secret (`rbac`) valid until 2027
- No current usage in the project (replaced by OIDC in Phase 4)

The presence of this Service Principal caused the security incident mentioned in Decision 4 and represented an unnecessary attack surface.

### Decision

**Delete the App Registration, revoke the client secret, and remove the role assignment.**

### Rationale

- The Service Principal was not used by any component after Phase 4
- Its permissions (Contributor at subscription) were broader than needed
- Its secret was stored in `.env` in plain text, creating a leak risk
- Removing it eliminates an orphaned credential

### Actions taken

1. Revoked the client secret `rbac` (`a94c2dd0-efc4-4d9d-8544-b7b80bf784cf`)
2. Removed the Contributor assignment at the subscription scope
3. Deleted the App Registration `58ce9313-b5df-4624-80ab-80dd16ab73cf`
4. Verified the deletion via `az ad app show`

### Consequences

**Positive:**
- No more orphaned credentials
- Reduced attack surface
- No more confusion about which identity is used in local development

**Negative:**
- None identified. The Service Principal was not in use.

---

## Alternatives Considered and Rejected

### Custom RBAC roles

Creating custom roles like `SRE-Databricks-Operator` was considered. Rejected because:

- The Azure built-in roles cover all project needs
- Custom roles require ongoing maintenance when services change
- Built-in roles are maintained by Microsoft and well-documented

Custom roles will be revisited if a specific need emerges (e.g., a role that allows reading secrets but not writing them, if built-in roles are insufficient).

### Private Endpoints for Key Vault

A Private Endpoint for Key Vault was considered to eliminate public network access. Deferred to a later phase because:

- The project's threat model does not include a determined attacker in the same network
- Provisioning a Private Endpoint requires subnet configuration, DNS zones, and validation
- The current setup already restricts access via RBAC

### Conditional Access policies

Azure AD Conditional Access policies (e.g., require MFA, restrict locations) were considered. Not applicable to Azure for Students subscriptions with a single user.

---

## References

- [Security Model](security-model.md) — full reference document
- [Phase 6 — Security](../phases/phase-6-security.md) — implementation record
- [ADR-001](adr-001-databricks-cluster-limitation.md) — Databricks cluster limitation
- [ADR-002](adr-002-observability-stack.md) — observability stack selection
- Microsoft documentation: Key Vault RBAC, Managed Identities, Workload Identity Federation

---

## Revision History

| Date | Change |
|------|--------|
| 2026-09-26 | Initial decisions recorded after Phase 6 |
