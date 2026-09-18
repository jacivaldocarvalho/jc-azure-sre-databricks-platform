# Documentation

Central documentation for the JC-Azure SRE Databricks Platform project.

## Structure

| Directory | Purpose |
|-----------|---------|
| `phases/` | Detailed record of each project phase (what, why, how, validation) |
| `architecture/` | Architecture Decision Records (ADRs) and diagrams |
| `operations/` | Runbooks and operational procedures |
| `troubleshooting/` | Guides for common issues and recovery |
| `conventions.md` | Project-wide standards and conventions |

## Quick Links

### Phases

- [Phase 0 — Foundation](phases/phase-0-foundation.md)
- [Phase 1 — Base Network](phases/phase-1-network.md)
- [Phase 2 — Databricks and Data Lake](phases/phase-2-databricks-data-lake.md)
- [Phase 3 — Data Pipeline](phases/phase-3-pipeline.md)

### Architecture Decision Records

- [ADR-001 — Databricks Cluster Limitation in Azure for Students](architecture/adr-001-databricks-cluster-limitation.md)

### Conventions

- [Project Conventions](conventions.md)

## How to Use This Documentation

Each phase document follows a consistent structure:

1. **Objective** — what the phase set out to accomplish
2. **Context** — preconditions and dependencies
3. **Implementation** — what was built and how
4. **Validation** — how to verify success
5. **Lessons Learned** — what changed and why
6. **Artifacts** — files, resources, and outputs produced

This consistency makes it easy to audit the project chronologically and to onboard new contributors.

## Audience

- **Recruiters and technical interviewers** — to assess the depth of technical decisions
- **Engineers replicating the setup** — to follow the phases step by step
- **Future self** — to remember why certain choices were made

## Related Documentation

- [Main README](../README.md) — project overview and quick start
- [CONTRIBUTING.md](../CONTRIBUTING.md) — how to contribute
