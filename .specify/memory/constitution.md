<!--
Sync Impact Report
Version change: template -> 1.0.0
Modified principles:
- template principle 1 -> I. Public Core Boundary
- template principle 2 -> II. Project-Local Workspace Portability
- template principle 3 -> III. Secret Safety
- template principle 4 -> IV. Agent-Neutral Interface
- template principle 5 -> V. Testable Spec-Driven Delivery
Added sections:
- Additional Constraints
- Development Workflow
Removed sections:
- Placeholder template sections
Templates requiring updates:
- updated: .specify/templates/plan-template.md
- updated: .specify/templates/spec-template.md
- updated: .specify/templates/tasks-template.md
Deferred items:
- none
-->
# VerifySignal Spec Constitution

## Core Principles

### I. Public Core Boundary

VerifySignal Spec MUST interact with VerifySignal Core only through documented
public CLI JSON contracts. Features that validate, run, inspect reports, or
check Core readiness MUST define the required public operation names, schema
names, schema versions, and incompatibility behavior. Private Core package
imports, private source inspection, undocumented report internals, and
implementation-specific response fields are prohibited.

Rationale: VerifySignal Spec is an open-source interface over a private Core.
The boundary must remain stable, reviewable, and safe for external clients.

### II. Project-Local Workspace Portability

Project state owned by VerifySignal Spec MUST live in the target repository and
MUST use `.verifysignal/` as the canonical workspace unless a future constitution
amendment changes the workspace contract. Workspace records MUST remain portable
across supported coding-agent integrations and deterministic non-AI CLI flows.
Generated run requests, reusable skills, registry records, run history, repair
state, and integration manifests MUST have explicit ownership and preservation
rules.

Rationale: Users should be able to move, review, commit, and run their use case
state without depending on one assistant, machine, or hidden global state.

### III. Secret Safety

Credential values and secret-looking runtime values MUST NOT be persisted in
workspace metadata, generated run requests, skills, logs, run history, repair
sessions, templates, or public summaries. Agents and commands MUST avoid
sensitive files by default and require explicit user approval before reading
local environment files or secret-bearing configuration. Features that handle
runtime inputs, project inspection, Core output, or repair suggestions MUST
include redaction and non-persistence tests.

Rationale: The product works inside user repositories and may invoke browser
runs with credentials. Secret handling must be deterministic and conservative.

### IV. Agent-Neutral Interface

Agent integrations MUST be adapters over the shared workspace and CLI contract,
not separate product implementations. MVP integrations are Codex and Claude
Code, but existing registered use cases MUST remain listable and runnable
without AI assistance. Integration install, upgrade, switch, and removal flows
MUST preserve user-modified managed files unless explicit replacement is
approved.

Rationale: VerifySignal Spec is the interface layer for VerifySignal use cases,
not a one-assistant workflow that locks users into generated files.

### V. Testable Spec-Driven Delivery

Every feature MUST be driven by prioritized, independently testable user stories
and MUST keep `spec.md`, `plan.md`, `contracts/`, and `tasks.md` consistent
before implementation. Public CLI behavior, workspace schema behavior, Core
compatibility behavior, secret safety behavior, and cross-agent portability
behavior MUST have contract, unit, integration, or documented repeatable manual
validation tasks before implementation is considered complete.

Rationale: The repository exists to make VerifySignal use cases repeatable.
Implementation work must remain traceable to executable behavior and reviewable
artifacts.

## Additional Constraints

- Repository documentation, generated workspace guidance, agent skill
  instructions, command help, and template text MUST be written in English.
- Conversations with maintainers MAY happen in other languages, but committed
  project artifacts MUST remain English.
- VerifySignal Spec SHOULD prefer local file workflows and bundled templates over
  network-dependent setup.
- New dependencies MUST be justified in `plan.md` and must not weaken the public
  Core boundary or secret-safety rules.

## Development Workflow

- `/speckit-specify` output MUST capture user value, independent tests,
  functional requirements, success criteria, edge cases, and assumptions.
- `/speckit-plan` output MUST evaluate each constitution principle before and
  after design and must document any complexity that cannot be avoided.
- `/speckit-tasks` output MUST include tests or repeatable validation tasks for
  public CLI contracts, workspace schema behavior, Core compatibility, secret
  handling, and any stated performance or usability criteria.
- `/speckit-analyze` SHOULD be run after task generation and before
  implementation. Critical or high-severity findings MUST be resolved or
  explicitly accepted by maintainers before `/speckit-implement`.
- Implementation MAY proceed story by story, but each completed story must pass
  its independent validation checkpoint before lower-priority stories are
  treated as complete.

## Governance

This constitution supersedes conflicting feature plans, task lists, templates,
and agent instructions in this repository. Amendments require an explicit
constitution update, a Sync Impact Report, and review of dependent templates and
active feature artifacts.

Versioning follows semantic versioning:

- MAJOR: Removes or redefines a principle in a way that changes existing
  obligations.
- MINOR: Adds a principle or materially expands governance requirements.
- PATCH: Clarifies wording without changing obligations.

Compliance review is required during planning and analysis. If a feature needs
to violate a principle, the feature must either change or the constitution must
be amended first.

**Version**: 1.0.0 | **Ratified**: 2026-05-25 | **Last Amended**: 2026-05-25
