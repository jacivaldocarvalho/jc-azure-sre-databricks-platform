# ADR-008 — Three-Environment Structure (dev, staging, prod)

**Status:** Accepted
**Date:** 2026-10-09 (recorded retroactively; decision made in Phase 0)
**Deciders:** Project author
**Context:** Phase 0 (Foundation)

---

## Context and Problem Statement

The Terraform code needs to be organized to support multiple
environments. The question is: how many environments, and with what
structure?

Common patterns:

- Single environment (everything in one place)
- Two environments (dev, prod)
- Three environments (dev, staging, prod)
- Per-developer environments
- Per-feature environments

---

## Options Considered

| Option | Description | Trade-offs |
|--------|-------------|------------|
| Single environment | One `main.tf` for everything | Simplest; not realistic |
| Two environments | `dev` and `prod` | Realistic; missing the pre-prod stage |
| **Three environments** | `dev`, `staging`, `prod` | Realistic; more files |
| Per-developer | One per developer | Complex for a solo project |
| Per-feature | One per feature branch | Very complex; not needed |

---

## Decision

Adopt a **three-environment structure** (`dev`, `staging`, `prod`),
even though only `dev` is provisioned in the current project.

---

## Rationale

1. **Realism.** Enterprise Azure projects typically have at least
   three environments. Adopting the structure demonstrates awareness
   of this practice.

2. **Forward compatibility.** If the project migrates to a paid
   subscription and additional environments become necessary, the
   structure is already in place.

3. **Isolation of concerns.** Each environment can have its own:
   - Terraform state file
   - Variables
   - Backend configuration
   - Deployment pipeline

4. **Cost.** The additional directories (`staging`, `prod`) do not
   cost anything. They are just empty scaffolding.

---

## Consequences

### Positive

- **Realistic structure.** The project mirrors enterprise practice.
- **Easy to extend.** Adding a new environment is a matter of
  duplicating the `dev` directory and adjusting variables.
- **Clear separation.** State, variables, and configuration are
  isolated per environment.

### Negative

- **Empty scaffolding.** The `staging` and `prod` directories are
  empty (only `.terraform` placeholders). This could be seen as
  unnecessary.

- **Overhead for a solo project.** A solo project with three
  environments might seem over-engineered.

### Mitigations

- The README documents that only `dev` is provisioned.
- The `cost-analysis.md` explains the reasoning.
- The structure is justified as "enterprise realism for a portfolio."

---

## Alternatives Considered and Rejected

### Single environment

Rejected because it does not demonstrate awareness of environment
separation, which is a common interview topic.

### Two environments

Rejected because staging is a common requirement in enterprise
workflows. Skipping it would reduce the realism.

### Per-developer environments

Rejected because the project has a single developer. Would add
complexity without benefit.

---

## References

- [Phase 0 — Foundation](../phases/phase-0-foundation.md)
- [Conventions](../conventions.md)
- Terraform documentation: managing multiple environments

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial decision recorded (retroactive) |
