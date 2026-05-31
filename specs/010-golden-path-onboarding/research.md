# Research: Golden Path Onboarding

## Decision: Keep first-run suitability separate from branch relevance

First-run recommendation will use a dedicated suitability score that optimizes
for the user's first successful experience. Branch relevance, recent git
changes, and business priority remain useful secondary signals but cannot
override first-run suitability.

**Rationale**: The dogfood failure showed that active-branch context can surface
the most relevant engineering feature while missing the simplest demonstrable
validation. A new user needs a low-risk proof first, then can choose deeper
branch-relevant flows afterward.

**Alternatives considered**:

- Use current priority/confidence as the first-run score: rejected because it
  selects complex authenticated flows too often.
- Ignore branch relevance entirely: rejected because users still need to see
  why the active feature was not selected first.

## Decision: Auto-prepare safe understanding from specify when missing

When `/proofsignal-specify` starts in a workspace with no understanding,
ProofSignal Spec should run or orchestrate safe repository understanding and
then resume first-run recommendation. It pauses only for host permissions or
sensitive boundaries.

**Rationale**: Missing understanding is normal during onboarding. Requiring the
user to manually run another command and restart the flow turns the first
interaction into a procedural failure.

**Alternatives considered**:

- Keep the existing "run understand manually" blocker: rejected because it
  breaks first-run momentum.
- Ask before every inspection step: rejected because repeated approvals were a
  major dogfood UX failure.

## Decision: Accepting the golden path starts a guided end-to-end flow

Acceptance should move the user through authoring, validation, execution, safe
repair when needed, and final outcome reporting. The flow records the current
stage and resumes from blockers.

**Rationale**: A first-run recommendation is valuable only if accepting it turns
into a real demonstration. Recording an alias and leaving the user with manual
commands undercuts the product promise.

**Alternatives considered**:

- Acceptance records only state: rejected because it still feels manual.
- Acceptance immediately runs without validation/repair stages: rejected
  because authoring coherence and safety boundaries remain necessary.

## Decision: Install guidance is both terminal output and local artifact

Integration install should show a visually scannable terminal summary and also
generate/update local integration guidance. Both surfaces should use clear
stage/status markers, summaries, and next actions, with plain-text fallback when
color or rich formatting is unavailable.

**Rationale**: Terminal-only guidance is easy to lose; file-only guidance is
easy to miss. The first install needs immediate instruction and durable local
reference.

**Alternatives considered**:

- Terminal only: rejected because users may need to revisit guidance later.
- Generated files only: rejected because a successful install should tell the
  user what to do next without requiring discovery.

## Decision: Normalize understanding input before persistence errors

Understanding persistence should fill source traceability where it can be
inferred from inventory, allow ordinary public metadata such as git hashes and
route paths, and return product-language blockers for invalid payloads.

**Rationale**: The user should not see the assistant reverse-engineer hidden
payload contracts. The CLI already knows enough to normalize common cases and
report actionable schema guidance.

**Alternatives considered**:

- Keep strict raw validation only: rejected because it exposes schema friction
  as onboarding failure.
- Disable secret detection around understanding: rejected because sensitive
  repository data still needs deterministic protection.

## Decision: Golden Path uses existing understanding freshness rules

Golden Path must not create a second stale-policy. For the first run, it uses
the existing understanding freshness checks and labels partial inventory. After
the first run, normal understand behavior continues.

**Rationale**: The user clarified that Golden Path is only the first run. Stale
handling belongs to the existing understanding workflow and should be improved
there rather than forked into a separate first-run policy.

**Alternatives considered**:

- Add a Golden Path-specific stale check: rejected because it would duplicate
  existing workflow semantics.
- Ignore stale state for first run: rejected because stale inventory can produce
  wrong recommendations.
