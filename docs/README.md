# Documentation

Central documentation for the JC-Azure SRE Databricks Platform project.

## Structure

| Directory | Purpose |
|-----------|---------|
| `phases/` | Detailed record of each project phase (what, why, how, validation) |
| `architecture/` | Architecture Decision Records (ADRs), security model, and diagrams |
| `operations/` | Runbooks, procedures, and post-apply checklists |
| `troubleshooting/` | Guides for common issues and recovery |
| `conventions.md` | Project-wide standards and conventions |

## Quick Links

### Phases

- [Phase 0 — Foundation](phases/phase-0-foundation.md)
- [Phase 1 — Base Network](phases/phase-1-network.md)
- [Phase 2 — Databricks and Data Lake](phases/phase-2-databricks-data-lake.md)
- [Phase 3 — Data Pipeline](phases/phase-3-pipeline.md)
- [Phase 4 — CI/CD with Azure DevOps](phases/phase-4-cicd.md)
- [Phase 5 — Observability](phases/phase-5-observability.md)
- [Phase 6 — Security](phases/phase-6-security.md)

### Architecture

- [Security Model](architecture/security-model.md) — reference document

### Architecture Decision Records

- [ADR-001 — Databricks Cluster Limitation in Azure for Students](architecture/adr-001-databricks-cluster-limitation.md)
- [ADR-002 — Observability Stack Selection](architecture/adr-002-observability-stack.md)
- [ADR-003 — Security Model Decisions](architecture/adr-003-security-model.md)

### Operations and Troubleshooting

- [Operations](operations/README.md) — runbooks and post-apply checklist
- [Troubleshooting](troubleshooting/README.md) — common issues and fixes
- [Conventions](conventions.md) — project standards

## How to Use This Documentation

Each phase document follows a consistent structure:

1. **Objective** — what the phase set out to accomplish
2. **Context** — preconditions, dependencies, and decisions
3. **Implementation** — what was built and how
4. **Validation** — how to verify success
5. **Lessons Learned** — what changed and why
6. **Artifacts** — files, resources, and outputs produced

ADRs follow the Nygard pattern: Status, Context, Decision, Consequences, Alternatives, References.

The security model is a reference document, organized by asset inventory, threat model, identities, role assignments, authentication flows, and limitations.

## Audience

- **Recruiters and technical interviewers** — to assess the depth of technical decisions
- **Engineers replicating the setup** — to follow the phases step by step
- **Future self** — to remember why certain choices were made

## Related Documentation

- [Main README](../README.md) — project overview and quick start
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute