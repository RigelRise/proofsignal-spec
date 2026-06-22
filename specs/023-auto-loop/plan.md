# Implementation Plan: Autonomous Grounded Authoring Loop (`/proofsignal-auto`)

**Branch**: `023-auto-loop` | **Date**: 2026-06-22 | **Spec**: [spec.md](./spec.md)
**Input**: `/specs/023-auto-loop/spec.md`

## Summary

Add a one-shot `/proofsignal-auto` command that has the host agent drive
`discover → draft → ground/correct → persist → validate → run → bounded repair`
in a single conversation, stopping only on five real-unknown/side-effect
conditions. Spec ships no LLM: autonomy is a tight installed prompt plus a thin
adapter method for Core's new `discover` operation, consumed as an OPTIONAL
capability. Builds on Core feature 016 (dynamic grounding).

## Technical Context

**Language/Version**: Python 3.13 (existing CLI)  
**Primary Dependencies**: stdlib + existing workspace/workflow modules; no new dependency  
**Storage**: `.proofsignal/` workspace via existing `workflow persist`  
**Testing**: pytest (unit) + end-to-end against the Core `discover-grounding-app` example  
**Project Type**: open Python CLI (`proofsignal`)  
**Constraints**: public Core boundary only; no LLM; additive; secret-safe  
**Scale/Scope**: one adapter method, one capability helper, one installed template + registration (small)

## Constitution Check

- **Public Core boundary**: `discover` reached only via `CoreAdapter` over the public CLI JSON contract; treated as OPTIONAL (`core_supports_discover`), never added to `REQUIRED_OPERATIONS` (would mark every current Core incompatible per `core/contracts.py:validate_version_response`). ✔
- **Project-local workspace portability**: artifacts via `workflow persist` into `.proofsignal/`; no new global state; deterministic non-AI path unchanged. ✔
- **Secret safety**: no credential/token/receipt/source persistence or printing; grounding output already redacted by Core; tests cover non-persistence. ✔
- **Agent-neutral interface**: `/proofsignal-auto` is additive, rendered identically for Claude + Codex via `render_workflow_skill_files`; `auto` is an orchestration command, NOT added to `WORKFLOW_STAGES`/`PERSISTABLE_STAGES`. ✔
- **Testable delivery**: spec→plan→tasks; unit tests for adapter argv, capability, template install; e2e loop against the example. ✔

No violations.

**Artifact-scope note (simplicity)**: data model + research are inlined here; separate `research.md`/`data-model.md`/`quickstart.md` omitted for this small additive feature (quickstart = the e2e loop in tasks.md).

## Project Structure

```text
specs/023-auto-loop/
├── spec.md
├── plan.md
└── tasks.md

src/proofsignal_spec/
├── core/adapter.py        # EDIT: add discover() (mirror run() at 110-133)
├── core/contracts.py      # EDIT: add core_supports_discover() (NOT REQUIRED_OPERATIONS)
├── integrations/base.py   # EDIT: add WorkflowCommandSpec("auto", ...) to WORKFLOW_COMMANDS
├── templates/agent-commands/proofsignal.auto.md   # NEW: the loop prompt
└── cli.py                 # EDIT (optional): `proofsignal discover` passthrough

tests/                     # adapter discover argv; core_supports_discover; template install
```

**Structure Decision**: reuse existing modules; the loop is orchestration via the
installed prompt + existing `workflow check/persist/validate/run/repair`. No new
engine subsystem is introduced for the MVP — the escalation gates the prompt
relies on already exist in `stage_persistence.py` (blocking questions, write
resource-identity) and are surfaced as STOP conditions by the prompt.

## Data Model (inlined)

- `core_supports_discover(version_response) -> bool`: scans
  `version_response["data"]["operations"]` for `{name: "discover", schema: "proofsignal.discover/v1"}`.
- `CoreAdapter.discover(*, url, skill, headed=False, env=None, entitlement_receipt=None) -> dict`.

## Existing Behavior Context

- **Related**: 002 proofsignal-workflow, 017 skill-execution-boundary, 018-021 write/side-effect safety (escalation rule 3 reuses `_require_resource_identity_for_new_write`), Core 016 discover.
- **Affected prior behavior**: none modified — additive command + additive adapter method + additive capability helper.
- **Regression validation**: existing pytest suite stays green; staged commands and deterministic flows unchanged.

## Complexity Tracking

*No violations.*
