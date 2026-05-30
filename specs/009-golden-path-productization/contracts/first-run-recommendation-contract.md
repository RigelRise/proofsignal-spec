# Contract: First-Run Recommendation

## Purpose

Expose a deterministic product-owned recommendation for the first golden-path
run. Agents render the recommendation in chat, but the ranking and status come
from ProofSignal Spec data.

## Proposed CLI surface

```text
proofsignal-spec workflow recommend-first-run --project <path> --json
proofsignal-spec workflow accept-first-run <alias> --project <path> --json
proofsignal-spec workflow skip-first-run --project <path> --json
```

The recommendation command reads project-local `.proofsignal/` state and safe
coverage inventory. It does not execute a browser run. Acceptance and skip
commands record golden-path state only; execution still happens through the
normal validated run command.

## JSON schema

`schemaVersion`: `proofsignal-spec-first-run-recommendation/v1`

Required fields:

- `status`: `ready`, `blocked`, `skipped`, or `unavailable`.
- `targetStatus`: `resolved`, `missing`, `unreachable`, or `unknown`.
- `recommendedCandidate`: Object or null.
- `rankedCandidates`: Ordered list of scored candidates.
- `recommendationText`: Strong user-facing recommendation when ready.
- `acceptancePrompt`: User prompt asking to accept or skip.
- `skipMeaning`: Explanation that skip is not success or failure.
- `stageCards`: Agent-chat stage cards for the recommendation stage.
- `nextAction`: Next CLI command or agent action.

`recommendedCandidate` fields:

- `alias`
- `surface`
- `behavior`
- `score`
- `rationale`
- `sourceInventoryItems`
- `knownRuntimeRequirements`

`rankedCandidates[]` fields:

- `alias`
- `rank`
- `score`
- `rationale`
- `blockers`
- `scoringSignals`

## Ranking rules

The top candidate must maximize first-run suitability:

1. Low setup risk.
2. Real reachable target.
3. No unresolved credential values.
4. Simple rendered-result evidence.
5. Low data dependency.
6. Fresh or complete inventory.
7. High confidence and priority.

## Blocking rules

Return `status: blocked` when:

- No real target has been selected or confirmed.
- The target is known to be unreachable.
- All candidates require unresolved credentials.
- All candidates depend on volatile or absent data.
- Coverage inventory is missing or stale and cannot support a recommendation.

## Secret safety

The command must reject or redact secret-looking target values. It must never
persist credential values, browser storage values, cookie values, or raw
sensitive payloads in recommendation text, scoring rationale, stage cards, or
artifacts.

## Acceptance semantics

When the user accepts, the selected alias becomes the first-run candidate. When
the user skips, the golden path is recorded as skipped and must not be counted
as success, failure, or inconclusive.

Acceptance output must include:

- `status: accepted`
- `selectedCandidate`
- `stageCards`
- `nextAction`

Skip output must include:

- `status: skipped`
- `skipMeaning`
- `stageCards`
- `nextAction`
