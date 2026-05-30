# Research: Golden Path Productization

## Decision: First-run recommendation is Spec-owned structured output

**Rationale**: The product must be responsible for identifying the simplest
stable first run. If the agent invents or loosely argues for a candidate, the
experience is not repeatable and cannot be tested. The recommendation should be
derived from coverage inventory, candidate metadata, runtime requirements, and
target readiness signals already available through public ProofSignal Spec
workspace records.

**Alternatives considered**:

- Agent-only recommendation: rejected because it is hard to test and varies by
  assistant.
- User-only candidate selection: rejected because it loses the guided golden
  path value.
- Automatic run without acceptance: rejected because the user must consent to
  the first run on their real target.

## Decision: Agent chat is the primary UX, backed by deterministic data

**Rationale**: The owner explicitly wants the impressive first-run experience in
chat. Codex and Claude should render strong stage cards from deterministic
fields so the primary presentation is rich while CLI JSON and workspace records
remain the source of truth.

**Alternatives considered**:

- Rich terminal only: rejected because the first-run product experience is
  agent-chat first.
- Local dashboard: rejected for MVP because it adds a separate runtime and UI
  surface.
- Secondary report as primary experience: rejected because reports support
  inspection but should not replace the chat journey.

## Decision: Standardized stage cards define the chat contract

**Rationale**: Stage cards make the UX testable. Each first-run step can be
checked for required fields: title, status marker, one-line summary, why it
matters, primary evidence, repair/change details when present, and next action.

**Alternatives considered**:

- Free-form rich narration: rejected because it is not reliably testable.
- Final summary only: rejected because the owner wants each step and result to
  be visually strong.
- Full technical logs: rejected because raw logs are supporting material, not
  the primary experience.

## Decision: First-run success states are strict and explicit

**Rationale**: The first run should convince the user that ProofSignal worked on
something real. Success is only `passed` or `repaired-passed`, both requiring
Core/browser success, complete Spec coverage, mapped rendered-result evidence
for all required gates, persisted artifacts, and a clear next action.

**Alternatives considered**:

- Treat actionable failure as success: rejected for the first run because the
  product should recommend a simple stable candidate.
- Treat report generation as success: rejected because it is not enough value.
- Treat declined recommendation as failure: rejected because the user can skip
  the golden path without product failure.

## Decision: Repair is part of first-run recovery, not a separate demo

**Rationale**: If the accepted first-run candidate fails for a repairable
artifact or flow reason, repair should classify, explain, fix, revalidate, rerun,
and then count success only after the final strict pass. If the first run passes
directly, no repair demonstration is needed.

**Alternatives considered**:

- Separate controlled repair demo after a pass: rejected because it feels fake
  and unnecessary.
- Natural failures only with no automated help: rejected because repair is a
  core product differentiator.
- Fake target repair fallback: rejected because fake/demo targets are not
  user-facing golden-path value.

## Decision: Safe mechanical repairs may auto-apply with boundaries

**Rationale**: The product should feel capable when it can fix a mechanical
issue without asking the user for every small edit. Auto-apply is allowed only
for selector specificity, wait strategy, ordering, target-specificity, and
equivalent flow fixes that preserve validation intent and produce before/after
feedback.

**Alternatives considered**:

- Ask before every repair: rejected because it weakens the product value and
  adds friction to safe mechanical fixes.
- Auto-apply all repairs: rejected because data, credential, gate, and expected
  behavior changes can alter validation intent.
- Suggest-only repair: rejected because it does not deliver the first-run value
  loop.

## Decision: Keep fake/demo targets internal to regression tests

**Rationale**: A user does not get product value from validating a fake app. The
MVP should guide the user to a real reachable target they care about. Fixtures
remain useful for deterministic automated tests and Core compatibility checks,
but they are not a user-facing fallback story.

**Alternatives considered**:

- Core fake auth app as MVP target: rejected because it validates the mechanism,
  not the user's product.
- Dual real plus fake MVP targets: rejected because it splits the experience and
  introduces unnecessary fallback framing.
- Staging-only target: rejected because the first run must work for the user's
  own project or chosen real target.

## Decision: Migrate 008 repair wording intentionally

**Rationale**: Feature 008 conservatively required confirmation for selector,
wait/flow, data, and coverage changes. Feature 009 narrows this: safe mechanical
selector/wait/flow repairs may auto-apply when they preserve intent, while data,
credential, required-gate, and expected-behavior changes still require recorded
confirmation.

**Alternatives considered**:

- Preserve 008 wording unchanged: rejected because it contradicts the clarified
  009 UX and repair autonomy.
- Remove confirmation entirely: rejected because it would weaken validation
  intent and secret safety.
