# Implementation Plan: Golden Path Productization

**Branch**: `009-golden-path-productization` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/009-golden-path-productization/spec.md`

## Summary

Productize the first ProofSignal Spec experience so a new user is strongly guided
to run the simplest stable validation candidate on a real target they care about,
sees each stage in a polished agent-chat-first format, and reaches a strict
validated pass directly or after a transparent safe repair cycle.

The technical approach keeps ProofSignal Core behind the public CLI JSON
contract. ProofSignal Spec owns first-run candidate ranking, first-run state,
stage-card presentation data, strict-pass classification, safe mechanical repair
autonomy, and generated agent guidance. Core continues to execute browser runs,
perform authoring checks, and inspect reports through documented operations only.

## Technical Context

**Language/Version**: Python 3.11+ package and CLI; Markdown/YAML/JSON workflow
artifacts; generated Codex and Claude agent instructions.
**Primary Dependencies**: Existing argparse CLI, pydantic-style dataclasses,
PyYAML, packaging, pathspec, pytest, Rich dependency already declared; no new
runtime dependency planned.
**Storage**: Project-local `.proofsignal/` workspace records, product context,
use-case records, run requests, skills, run history, repair sessions, and
generated `specs/009-golden-path-productization/` design artifacts.
**Testing**: pytest contract, unit, and integration tests with temporary target
workspaces plus the existing fake Core fixture for deterministic regression
coverage. Real-target golden-path behavior is validated through repeatable
workspace scenarios, not private Core internals.
**Target Platform**: Local developer workspaces on macOS/Linux; Codex and Claude
agent chats as primary guided surfaces; deterministic CLI as equivalent
non-agent fallback.
**Project Type**: Packaged Python CLI and workflow orchestration layer with
generated agent templates and project-local managed artifacts.
**Performance Goals**: First-run candidate ranking completes in under 1 second
after inventory is available; stage-card generation adds under 100ms to
workflow/run/repair output; validation readiness does not execute the full
browser flow; first accepted golden path reaches strict pass in 10 minutes or
less when the target is reachable and the candidate is stable.
**Constraints**: Public Core CLI JSON only; no private Core imports or
undocumented report internals; real-target-first user journey; no fake/demo
target as user fallback; no ad hoc run-time `--baseUrl` override; no persisted
credential values; raw logs cannot be the primary UX; required gates cannot be
weakened by repair without explicit recorded intent change.
**Scale/Scope**: Multiple target projects, each with one `.proofsignal/`
workspace, many candidate use cases, one recommended first-run candidate at a
time, and reusable skills shared across run requests.

**ProofSignal Core Public Contract**: This feature depends on
`proofsignal-public-cli-json/v1`. Required Core operations are `version`,
`authoring-check`, `run`, and `report.inspect`. Required schemas are
`proofsignal.version/v1`, `proofsignal.authoring-check/v1`,
`proofsignal.run/v1`, and `proofsignal.report-inspection/v1`. Missing or
incompatible operations/schemas must produce classified blockers and must not
fall back to private Core packages, installed package source inspection, or
undocumented report internals.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Public Core boundary**: PASS. The plan adds Spec-owned first-run ranking,
  stage-card rendering data, and repair decisions on top of documented
  workflow/Core JSON outputs only.
- **Project-local workspace portability**: PASS. First-run recommendation,
  acceptance/skipped state, run status, repair feedback, and stage-card evidence
  are derived from or recorded in `.proofsignal/` workspace records.
- **Secret safety**: PASS. Target URLs are treated as locators and scanned for
  secret-looking values. Credential values remain references or runtime-only
  inputs and are never persisted in recommendations, repair feedback, logs, or
  stage cards.
- **Agent-neutral interface**: PASS with an explicit UX priority. Codex and
  Claude chat are the primary polished surfaces, while deterministic CLI JSON
  and workspace records remain the source of truth and preserve equivalent
  non-AI semantics.
- **Testable spec-driven delivery**: PASS. The feature has independently
  testable contracts for first-run recommendation, agent-chat stage cards,
  strict-pass status, repair autonomy, secret safety, Core compatibility, and
  regression behavior.

## Project Structure

### Documentation (this feature)

```text
specs/009-golden-path-productization/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   |-- agent-chat-stage-card-contract.md
|   |-- first-run-recommendation-contract.md
|   |-- golden-path-run-result-contract.md
|   |-- golden-path-workspace-state-contract.md
|   `-- repair-autonomy-contract.md
|-- checklists/
|   `-- requirements.md
`-- tasks.md
```

### Source Code (repository root)

```text
src/proofsignal_spec/
|-- commands/
|   |-- workflow.py
|   |-- run.py
|   |-- repair.py
|   `-- validate.py
|-- workflows/
|   |-- coverage_inventory.py
|   |-- first_run.py              # new: recommendation scoring and state
|   |-- stage_cards.py            # new: chat stage-card data builders
|   |-- repair_recommendations.py
|   |-- repair_classification.py
|   |-- models.py
|   |-- repository.py
|   `-- stage_documents.py
|-- integrations/
|   |-- codex.py
|   `-- claude.py
|-- templates/
|   |-- agent_guidance.py
|   |-- agent-commands/
|   `-- agent-skills/
|-- core/
|   |-- adapter.py
|   `-- contracts.py
`-- workspace/
    |-- models.py
    |-- repository.py
    `-- validation.py

tests/
|-- contract/
|-- integration/
|-- unit/
`-- fixtures/
```

**Structure Decision**: Extend the existing single Python CLI/workflow package.
Do not add a web dashboard, separate app, or database. First-run recommendation
and stage-card data live in `workflows/`; CLI subcommands expose deterministic
JSON; Codex/Claude templates render the chat-first experience from those public
fields.

## Phase 0: Research

Research decisions are captured in [research.md](./research.md):

- First-run recommendation must be Spec-owned structured output, not agent-only
  judgment.
- The primary first-run UX is agent chat rendered from standardized stage-card
  data, while CLI JSON remains the source of truth.
- A first run succeeds only as `passed` or `repaired-passed` after strict Core
  and Spec coverage criteria are met; declined recommendations are `skipped`.
- Safe mechanical repairs may auto-apply only when they preserve validation
  intent and produce clear before/after feedback.
- Real-target-first behavior requires target confirmation before planning or
  execution; fake/demo targets are limited to internal regression fixtures.
- Existing 008 confirmation-gated repair wording must be intentionally migrated
  to the 009 safe-autonomy policy.

## Phase 1: Design & Contracts

Design outputs:

- [data-model.md](./data-model.md): first-run recommendation, candidate score,
  agent-chat stage card, golden-path run state, repair feedback, and workspace
  state extensions.
- [contracts/first-run-recommendation-contract.md](./contracts/first-run-recommendation-contract.md):
  public JSON shape and ranking semantics for recommending the first run.
- [contracts/agent-chat-stage-card-contract.md](./contracts/agent-chat-stage-card-contract.md):
  required stage-card fields and rendering rules for Codex/Claude guidance.
- [contracts/golden-path-run-result-contract.md](./contracts/golden-path-run-result-contract.md):
  accepted, skipped, passed, repaired-passed, failed, blocked, and incomplete
  first-run status semantics.
- [contracts/golden-path-workspace-state-contract.md](./contracts/golden-path-workspace-state-contract.md):
  public inspect/reset semantics for Golden Path Workspace State, including
  preserved artifacts and reset previews.
- [contracts/repair-autonomy-contract.md](./contracts/repair-autonomy-contract.md):
  safe mechanical auto-apply categories, confirmation-required categories,
  before/after feedback, revalidation, and rerun requirements.
- [quickstart.md](./quickstart.md): repeatable verification guide for
  recommendation ranking, stage-card UX, run status, repair autonomy, and
  regression coverage.

## Post-Design Constitution Check

- **Public Core boundary**: PASS. Contracts define Spec-owned interpretation and
  presentation of public workflow/Core outputs only.
- **Project-local workspace portability**: PASS. New first-run and repair state
  is represented in portable workspace records and generated artifacts.
- **Secret safety**: PASS. Data model and contracts explicitly prohibit
  persisted credentials, secret-looking URLs, browser storage, cookies, and raw
  sensitive payloads in stage cards or repair feedback.
- **Agent-neutral interface**: PASS. Agent chat is the polished primary UX, but
  CLI JSON contracts and workspace records remain deterministic and equivalent.
- **Testable spec-driven delivery**: PASS. Quickstart and contracts define
  focused tests for ranking, skip/pass/repaired-pass status, stage cards,
  repair autonomy, Core compatibility, secret safety, and existing workflow
  regressions.

## Complexity Tracking

No constitution gate requires a complexity exception. The feature adds
structured recommendation and presentation layers inside existing workflow,
template, and repair modules rather than introducing a separate UI runtime.
