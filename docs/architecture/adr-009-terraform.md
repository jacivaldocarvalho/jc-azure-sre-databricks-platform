# ADR-009 — Terraform as Infrastructure as Code

**Status:** Accepted
**Date:** 2026-10-09 (recorded retroactively; decision made in Phase 0)
**Deciders:** Project author
**Context:** Phase 0 (Foundation)

---

## Context and Problem Statement

The project requires Infrastructure as Code (IaC) to provision and
manage Azure resources reproducibly. Several IaC tools are available:

- ARM Templates (JSON, Azure-native)
- Bicep (DSL, Azure-native)
- Terraform (HCL, multi-cloud)
- Pulumi (general-purpose languages)
- Ansible (configuration management)
- Chef, Puppet (configuration management)

The choice affects the entire project: how resources are defined,
how state is managed, how changes are reviewed, and how the code
is tested.

---

## Options Considered

| Tool | Language | Cloud support | State management | Community |
|------|----------|---------------|------------------|-----------|
| ARM Templates | JSON | Azure only | Azure-managed | Microsoft |
| Bicep | Bicep DSL | Azure only | Azure-managed | Microsoft |
| **Terraform** | HCL | Multi-cloud | Self-managed | Large |
| Pulumi | Python/TS/Go | Multi-cloud | Self-managed | Growing |
| Ansible | YAML | Multi-cloud | None | Large |

---

## Decision

Use **Terraform**.

---

## Rationale

1. **Market adoption.** Terraform is the most widely used IaC tool in
   the industry. Demonstrating proficiency with it is valuable for
   a DevOps/SRE portfolio.

2. **Multi-cloud.** Terraform supports Azure, AWS, GCP, and other
   providers with the same workflow. This makes the skills portable.

3. **State management.** Terraform's state model (with remote backends)
   is well-suited for team workflows and demonstrates mature practices.

4. **Module system.** Terraform modules enable reusable, composable
   infrastructure. The project uses 8 modules, demonstrating this.

5. **Community and documentation.** Terraform has extensive
   documentation, examples, and community support.

6. **Job market.** Terraform is frequently mentioned in SRE and
   DevOps job descriptions.

---

## Consequences

### Positive

- **Portable skills.** The Terraform knowledge transfers to other
  clouds and organizations.
- **Modular structure.** The project uses 8 modules with clear
  interfaces.
- **State isolation.** Each environment has its own state file.
- **Reproducibility.** The infrastructure can be recreated from
  code at any time.

### Negative

- **State management overhead.** The state file must be protected
  (which is why ADR-006 exists).
- **Separate tooling.** Terraform is a separate tool from the Azure
  CLI. The project requires both.
- **Not Azure-native.** Bicep and ARM have better integration with
  the Azure portal and Azure Policy.

### Mitigations

- The state backend is protected with versioning and soft delete
  (Phase 9).
- The Makefile wraps Terraform commands to simplify usage.
- The ADRs document the reasoning for each decision.

---

## Alternatives Considered and Rejected

### Bicep

Considered. Bicep is Azure-native and has excellent integration with
the Azure portal. However, it is Azure-only, which reduces the
portability of the skills. Rejected in favor of Terraform.

### ARM Templates

Rejected because of the verbose JSON syntax and the lack of a modern
development experience (limited IDE support, no state management).

### Pulumi

Considered. Pulumi allows using general-purpose languages (Python,
TypeScript). However, the community is smaller and the tool is less
established. Rejected in favor of Terraform's maturity.

### Ansible

Rejected because Ansible is primarily a configuration management tool,
not an infrastructure provisioning tool. It lacks a proper state model
for infrastructure.

---

## References

- [Phase 0 — Foundation](../phases/phase-0-foundation.md)
- [Conventions](../conventions.md)
- [ADR-006 — Disaster Recovery Strategy](adr-006-dr-strategy.md)
- Terraform documentation

---

## Revision History

| Date | Change |
|------|--------|
| 2026-10-09 | Initial decision recorded (retroactive) |
