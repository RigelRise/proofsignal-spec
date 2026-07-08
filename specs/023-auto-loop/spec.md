# Feature Specification: Autonomous Grounded Authoring Loop (`/verifysignal-auto`)

**Feature Branch**: `023-auto-loop`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: User description: "A one-shot autonomous loop where the host agent drives discover (Core 016 dynamic grounding) → author → validate → run → repair in a single pass with minimal user stops, escalating only on real unknowns or write side-effects. Spec ships no LLM; autonomy = a tight installed agent command plus an optional Core grounding capability consumed via the public contract."

## Constitution Alignment *(mandatory)*

- **Public Core boundary**: The loop calls Core's new `discover` operation only through the public CLI JSON contract via `CoreAdapter`; `discover` is treated as an OPTIONAL capability (it is NOT added to `REQUIRED_OPERATIONS`), discovered by inspecting the public `version` operations array (`core_supports_discover`). No private Core imports or undocumented internals.
- **Project-local workspace portability**: The loop persists artifacts only through the existing `workflow persist` path into `.verifysignal/`; it introduces no new global state. Existing deterministic, non-AI flows (`author`/`validate`/`run`) remain usable unchanged.
- **Secret safety**: The loop never persists or prints credential values, tokens, receipts, signed URLs, screenshots, or source snapshots; grounding output is already redacted by Core; credential resolution stays on the existing protected path.
- **Agent-neutral interface**: `/verifysignal-auto` is an additive AI-only convenience installed as an adapter over the shared workspace + CLI contract, rendered identically for Claude and Codex. It orchestrates existing stages; it does not replace the deterministic CLI, and registered use cases remain listable/runnable without AI.
- **Testable delivery**: `CoreAdapter.discover` argv, `core_supports_discover` true/false, and template installation are unit-tested; the end-to-end loop is validated against the Core `discover-grounding-app` example.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One-pass grounded authoring to a green run (Priority: P1)

As a developer using Claude Code or Codex, I want a single `/verifysignal-auto "<goal> against <url>"` command that drafts a browser use case from my source, grounds its selectors against the live app, applies the grounded corrections, validates, runs, and (when safe) auto-repairs — stopping only when it genuinely needs my input — so I reach a green validation in one conversation instead of stepping through nine stages.

**Why this priority**: This is the entire value of the feature and the smallest demonstrable slice.

**Independent Test**: Run `/verifysignal-auto` against the Core `discover-grounding-app`; the agent drafts targets, `discover` corrects the divergent ones, the use case persists, validates, and `run` reports passed — with at most a credential prompt as a stop.

**Acceptance Scenarios**:

1. **Given** Core supports `discover` and a reachable target URL, **When** the agent drafts a skill and runs the loop, **Then** divergent selectors are corrected from `discover` output before the first `run` and the run reports `passed`.
2. **Given** `discover` reports a target still `not-found`/ambiguous with no confident correction, **When** the loop reaches that target, **Then** it STOPS and asks the user which element is meant (no invented selectors).
3. **Given** the use case is a write/external-notification class without a resolved `resourceIdentity`, **When** the loop reaches run preparation, **Then** it STOPS and requires explicit confirmation before any mutating run.
4. **Given** validation reports a missing required credential, **When** the loop reaches validation, **Then** it STOPS and asks the user to provide it (values are never persisted).
5. **Given** a run fails on a deterministic target issue, **When** the loop classifies the failure as a safe selector re-scope, **Then** it applies the fix and reruns, bounded to 2 attempts before escalating.

### User Story 2 - Graceful degrade when Core lacks grounding (Priority: P2)

As a user whose installed Core predates dynamic grounding, I want `/verifysignal-auto` to detect that `discover` is unavailable and either tell me to upgrade or continue source-only, rather than fail opaquely.

**Why this priority**: Keeps the loop safe across Core versions; P1 still delivers value on a current Core.

**Independent Test**: With a Core `version` response lacking the `discover` operation, `core_supports_discover` returns false and the loop reports an upgrade recommendation.

**Acceptance Scenarios**:

1. **Given** a Core `version` response without a `discover` operation entry, **When** the loop checks capability, **Then** `core_supports_discover` is false and the agent is instructed to recommend upgrading Core (or proceed source-only without the grounding boost).

### Edge Cases

- Unresolved `baseUrl`/target → STOP (escalation rule 1), never guess a URL.
- A target only present mid-flow → reported by `discover` as `not-found` on the entry URL; the loop escalates rather than inventing a selector.
- The deterministic non-AI path (`verifysignal run <alias>`) must keep working unchanged when `/verifysignal-auto` is not used.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `CoreAdapter` MUST expose a `discover(url, skill, ...)` method that invokes the Core `discover` operation via the public CLI JSON contract (mirroring `run`), returning the parsed JSON envelope.
- **FR-002**: Spec MUST provide `core_supports_discover(version_response)` that returns true only when the `version` operations array contains a `discover` entry with schema `verifysignal.discover/v1`; it MUST NOT be added to `REQUIRED_OPERATIONS`.
- **FR-003**: An installed `/verifysignal-auto` command MUST be rendered for both Claude and Codex from a single template and MUST drive: confirm capability → draft from source → ground via `discover` → apply corrections → persist via `workflow persist` → validate → run → bounded safe auto-repair.
- **FR-004**: The loop MUST STOP and ask the user on each of the five escalation conditions: unresolved baseUrl/target; missing credentials; write/external-notification class without resolved `resourceIdentity`; grounding still unresolved after correction; run still failing after 2 safe auto-repairs or a repair routed to clarify/plan.
- **FR-005**: The loop MUST persist artifacts only through `workflow persist`; it MUST NOT write managed `.verifysignal/` artifacts directly and MUST NOT persist credential values.
- **FR-006**: `/verifysignal-auto` MUST be additive: existing staged commands, `WORKFLOW_STAGES`, and the deterministic non-AI path MUST remain unchanged (`auto` is an orchestration command, not a persistable stage).
- **FR-007**: When `core_supports_discover` is false, the loop MUST recommend upgrading Core or proceeding source-only, not fail opaquely.

### Quality and Operability Requirements

- **NFR-001**: Acceptance scenarios validated via unit tests (`discover` argv, capability true/false, template install) and the end-to-end loop against the Core example app.
- **NFR-002**: Failure handling — capability-absent, unresolved target, missing credentials, and repeated run failure all surface as explicit STOP-and-ask outcomes, not silent continuation.
- **NFR-003**: Secret safety — no credential values, tokens, receipts, signed URLs, screenshots, or source snapshots are persisted or printed; redaction/non-persistence covered by tests.
- **NFR-004**: Existing behavior — staged commands and deterministic flows keep passing; `auto` is additive.

### Key Entities

- **Discover capability**: derived from the Core `version` operations array; optional, schema `verifysignal.discover/v1`.
- **Escalation outcome**: a STOP result naming the blocker and the recovery action.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Against the Core `discover-grounding-app`, `/verifysignal-auto` produces one grounded green run with at most one user stop (credentials).
- **SC-002**: With a `discover`-less Core `version` response, `core_supports_discover` is false and the loop reports an upgrade path rather than crashing.
- **SC-003**: No credential value, token, or source snapshot is persisted by the loop in any test.
- **SC-004**: Installing the Claude or Codex integration produces a `verifysignal-auto/SKILL.md`.

## Assumptions

- Core 016 (dynamic grounding `discover`) is available on a current Core; `/verifysignal-auto` degrades gracefully otherwise.
- The host agent (Claude/Codex) is the only runtime that performs reasoning; Spec ships no LLM and only shapes state + delegates to Core.
- The MVP grounds against a single `--url`; multi-step/authed grounding is deferred with Core 016.
