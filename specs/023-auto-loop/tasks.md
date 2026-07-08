---
description: "Task list for Autonomous Grounded Authoring Loop (023)"
---

# Tasks: Autonomous Grounded Authoring Loop (`/verifysignal-auto`)

**Input**: `/specs/023-auto-loop/` (spec.md, plan.md)

**Tests**: Validation tasks REQUIRED per story; write failing tests before code.

## Phase 1: Setup / Foundational

- [ ] T001 Confirm Core 016 `discover` is available (`verifysignal core version --json` operations include `discover`); confirm `core/contracts.py:REQUIRED_OPERATIONS` is the existing 5 and must NOT gain `discover`.

## Phase 2: User Story 1 - One-pass grounded loop (P1) 🎯 MVP

### Tests (write first, must fail) ⚠️

- [ ] T002 [P] [US1] `tests/.../test_core_adapter_discover.py`: `CoreAdapter.discover(url=..., skill=...)` builds argv `["discover","--url",url,"--skill",skill,"--json"]` and calls `require_compatible()` then `_run`.
- [ ] T003 [P] [US1] `tests/.../test_auto_template_install.py`: `render_workflow_skill_files` for Claude and Codex includes `verifysignal-auto/SKILL.md`; `auto` is NOT in `WORKFLOW_STAGES`/`PERSISTABLE_STAGES`.

### Implementation

- [ ] T004 [US1] `core/adapter.py`: add `discover(*, url, skill, headed=False, env=None, entitlement_receipt=None)` mirroring `run` (110-133). (FR-001)
- [ ] T005 [US1] `cli.py` (optional): add a `verifysignal discover --url --skill --json` passthrough calling `CoreAdapter.discover`. (FR-001)
- [ ] T006 [US1] `integrations/base.py`: add `WorkflowCommandSpec("auto", "Drive discover → author → run → repair in one pass", "<goal or alias>")` to `WORKFLOW_COMMANDS`. Do NOT touch `WORKFLOW_STAGES`. (FR-003, FR-006)
- [ ] T007 [US1] New `templates/agent-commands/verifysignal.auto.md`: the tight loop prompt (capability check → draft → discover/correct → persist implement → validate → run → bounded safe repair) with the five escalation STOP rules and verbatim secret-safety guardrails. (FR-003, FR-004, FR-005)

## Phase 3: User Story 2 - Graceful degrade (P2)

### Tests (write first, must fail) ⚠️

- [ ] T008 [P] [US2] `tests/.../test_core_supports_discover.py`: true for a version response with the discover op; false without it; false for wrong schema.

### Implementation

- [ ] T009 [US2] `core/contracts.py`: add `core_supports_discover(version_response) -> bool` scanning the operations array; do NOT add `discover` to `REQUIRED_OPERATIONS`. Reference it from the auto template's capability check. (FR-002, FR-007)

## Phase 4: Validation

- [ ] T010 Run the full pytest suite; confirm existing staged-command, write-safety, and deterministic-flow tests stay green (NFR-004).
- [ ] T011 End-to-end: against the Core `discover-grounding-app`, drive the loop (manually or scripted) → one grounded green run with ≤1 user stop (SC-001); a `discover`-less version response degrades (SC-002).

## Dependencies

- US1 (P1) is the MVP. US2 (P2) is additive. Core 016 must ship first. Tests precede implementation.

## Notes

- `workflow persist` stays the only artifact-write path; never persist credentials (FR-005).
- No invented selectors; unresolved grounding escalates (FR-004 rule 4).
