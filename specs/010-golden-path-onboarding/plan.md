# Implementation Plan: Golden Path Onboarding

**Branch**: `010-golden-path-onboarding` | **Date**: 2026-05-31 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/010-golden-path-onboarding/spec.md`

## Summary

Refine the Golden Path first-run product experience from a useful capability
into a smooth onboarding path. The feature closes the dogfood gaps observed when
a new target repository had no `.verifysignal/` understanding yet, the first-run
candidate ranking over-weighted active branch relevance, integration install
produced no clear user guide, normal commit identifiers were treated as
secret-looking, and agent authoring had to discover payload shape by trial and
error.

The technical approach extends the `009-golden-path-productization` foundation
instead of replacing it. VerifySignal Spec will own a deterministic onboarding
orchestrator around existing workflow stages, a stronger first-run suitability
score that favors trivial stable rendered behavior over branch relevance,
visually rich install and stage guidance, safer understanding persistence and
inventory completion semantics, and a guided end-to-end accepted-first-run state
machine. VerifySignal Core remains behind the documented public CLI JSON
contract.

## Technical Context

**Language/Version**: Python 3.11+ package and CLI; Markdown/YAML/JSON workflow
artifacts; generated Codex and Claude agent instructions.  
**Primary Dependencies**: Existing argparse CLI, dataclasses, PyYAML,
packaging, pathspec, Rich, pytest, and the current fake Core fixture; no new
runtime dependency planned.  
**Storage**: Project-local `.verifysignal/` workspace records, product context,
coverage inventory, golden-path state, integration manifests, generated agent
guidance, and `specs/010-golden-path-onboarding/` design artifacts.  
**Testing**: pytest contract, unit, and integration tests with temporary target
workspaces; existing fake Core fixture for run/repair/readiness behavior; no
private Core package imports.  
**Target Platform**: Local developer workspaces on macOS/Linux; Codex and Claude
agent chats as primary onboarding surface; deterministic CLI JSON as equivalent
non-AI fallback.  
**Project Type**: Packaged Python CLI and workflow orchestration layer with
generated agent templates and project-local managed artifacts.  
**Performance Goals**: First-run recommendation remains under 1 second after
inventory is available; install guidance rendering adds under 100ms; clean
repository specify onboarding reaches first-run recommendation in under 3
minutes when safe local inspection is allowed.  
**Constraints**: Public Core CLI JSON only; no private Core imports or
undocumented report internals; no fake/demo target as user-facing fallback; no
credential persistence; respect existing understanding freshness rules; first
run only, normal workflow behavior resumes after the Golden Path is accepted,
skipped, blocked, or completed.  
**Scale/Scope**: Multiple target projects; each project has one `.verifysignal/`
workspace, many inventory candidates, one accepted or skipped Golden Path
choice, and reusable skills/run requests shared with ordinary workflows.

**VerifySignal Core Public Contract**: This feature continues to depend on
`verifysignal-public-cli-json/v1`. Required Core operations remain `version`,
`authoring-check`, `run`, and `report.inspect` through existing Spec adapters.
New onboarding behavior must classify missing/incompatible Core as a blocker and
must not inspect Core internals.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Public Core boundary**: PASS. The new orchestration, ranking, install
  guidance, and understanding-persistence behavior are Spec-owned. Any Core
  readiness or execution signal comes through existing public CLI JSON
  operations.
- **Project-local workspace portability**: PASS. Golden-path choice, guided-flow
  stage, inventory freshness, install guidance references, and outcome state
  stay in `.verifysignal/` or generated project-local integration files.
- **Secret safety**: PASS. The plan explicitly repairs false positives for
  ordinary public identifiers while keeping credential fields, URLs with secret
  query parameters, local env files, cookies, browser storage, and raw sensitive
  payloads non-persistable.
- **Agent-neutral interface**: PASS. Agents render a richer chat-first
  experience, but CLI JSON/state contracts own recommendation, accept/skip,
  guided-flow, and blocker semantics.
- **Testable spec-driven delivery**: PASS. Each story maps to contract,
  integration, or unit tests covering first-run ranking, missing-understanding
  onboarding, install guidance, understanding persistence, guided-flow state,
  and secret-safety regressions.

## Project Structure

### Documentation (this feature)

```text
specs/010-golden-path-onboarding/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- guided-first-run-flow-contract.md
|   |-- first-run-suitability-contract.md
|   |-- integration-onboarding-guidance-contract.md
|   `-- understanding-onboarding-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/verifysignal_spec/
|-- cli.py
|-- commands/
|   |-- workflow.py
|   |-- integration.py
|   |-- run.py
|   |-- repair.py
|   `-- validate.py
|-- workflows/
|   |-- first_run.py
|   |-- stage_cards.py
|   |-- coverage_inventory.py
|   |-- stage_persistence.py
|   |-- prerequisites.py
|   |-- models.py
|   `-- repository.py
|-- integrations/
|   |-- codex.py
|   |-- claude.py
|   |-- base.py
|   `-- manifests.py
|-- templates/
|   |-- agent_guidance.py
|   |-- agent-commands/
|   `-- agent-skills/
|-- workspace/
|   |-- validation.py
|   |-- product_context.py
|   |-- layout.py
|   `-- repository.py
`-- core/
    |-- adapter.py
    `-- contracts.py

tests/
|-- contract/
|-- integration/
|-- unit/
`-- fixtures/
```

**Structure Decision**: Extend the existing single Python CLI/workflow package.
Do not add a dashboard, server, new database, or new agent-specific product
logic. `workflows/first_run.py` owns recommendation and guided-flow state,
`workflows/coverage_inventory.py` and `stage_persistence.py` own inventory
normalization and persistence, `commands/integration.py` plus integration
renderers own install-time guidance, and templates render the chat-first
experience from public fields.

## Complexity Tracking

No constitution gate requires a complexity exception. The feature is additive to
the existing 009 Golden Path layer and narrows behavior from observed dogfood
failures rather than adding a separate runtime.

## Phase 0: Research

Research decisions are captured in [research.md](./research.md):

- First-run suitability must be a separate score from branch relevance and
  business priority.
- Missing understanding during specify should auto-prepare safe understanding
  and resume the original first-run flow when host permissions allow.
- Accepting a first run should start a guided end-to-end state machine, not only
  record a selected alias.
- Install guidance must appear in terminal output and generated local guidance,
  with rich markers and plain-text fallback.
- Understanding persistence should normalize source traceability and public
  metadata instead of exposing schema-trial friction to the user.
- Golden Path uses existing understanding freshness rules and applies only to
  the first run.

## Phase 1: Design & Contracts

Design outputs:

- [data-model.md](./data-model.md): first-run suitability, branch relevance,
  ideal-criteria gap, guided first-run state, onboarding guidance, and
  understanding inventory result extensions.
- [contracts/first-run-suitability-contract.md](./contracts/first-run-suitability-contract.md):
  deterministic ranking rules that favor trivial, public, stable rendered
  behavior and demote credential-heavy or branch-only relevance.
- [contracts/guided-first-run-flow-contract.md](./contracts/guided-first-run-flow-contract.md):
  accept/skip, guided stage transitions, blocker/resume behavior, and final
  outcome semantics.
- [contracts/integration-onboarding-guidance-contract.md](./contracts/integration-onboarding-guidance-contract.md):
  terminal and generated guidance shape, visual markers, color fallback, and
  install result fields.
- [contracts/understanding-onboarding-contract.md](./contracts/understanding-onboarding-contract.md):
  safe auto-prepare behavior, source traceability normalization, public metadata
  secret-safety allowlist, inventory completion/partial labeling, and stale
  freshness integration.
- [quickstart.md](./quickstart.md): repeatable verification guide for the
  ranking, specify onboarding, install guidance, accepted-flow state, and
  understanding persistence scenarios.

## Post-Design Constitution Check

- **Public Core boundary**: PASS. Contracts add Spec-owned onboarding and
  workspace behavior; Core remains accessed only through existing public
  adapter operations and schemas.
- **Project-local workspace portability**: PASS. New state is represented as
  portable workspace records and generated integration files. No hidden
  assistant/session state is authoritative.
- **Secret safety**: PASS. The data model and contracts preserve conservative
  redaction while explicitly allowing normal git hashes, branch names, route
  paths, and file paths as public metadata.
- **Agent-neutral interface**: PASS. Terminal/chat rendering is richer, but JSON
  contracts expose equivalent status, evidence, guidance, and next action.
- **Testable spec-driven delivery**: PASS. Quickstart and contracts define
  focused tests for first-run ranking, auto-prepare, install UX, guided-flow
  state, inventory completeness, secret safety, and regressions from 009.
