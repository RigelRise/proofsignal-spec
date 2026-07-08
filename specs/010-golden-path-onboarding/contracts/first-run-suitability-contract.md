# Contract: First-Run Suitability

## Purpose

Define how VerifySignal Spec chooses the first Golden Path run. This contract
separates "best first run" from branch relevance, product priority, or recent
git activity.

## CLI surface

```text
verifysignal-spec workflow recommend-first-run --project <path> --json
```

This command is read-only. It may inspect project-local `.verifysignal/`
understanding state and safe product context. It must not execute browser runs.

## JSON shape

`schemaVersion`: `verifysignal-spec-first-run-recommendation/v1`

Required fields:

- `status`: `ready`, `blocked`, `skipped`, or `unavailable`.
- `recommendedCandidate`: Candidate object or null.
- `rankedCandidates`: Ordered first-run suitability scores.
- `branchRelevantCandidates`: Candidates tied to active branch or recent work
  that were not selected first.
- `idealCriteria`: The ideal first-run criteria used for scoring.
- `recommendationText`: Assertive first-run recommendation text.
- `acceptancePrompt`: Prompt explaining that accepting is highly recommended.
- `explicitAcceptanceRequired`: Boolean.
- `stageCards`: Chat-first cards for rendering.
- `nextAction`: Next command or agent action.

`rankedCandidates[]` must include:

- `candidateAlias`
- `rank`
- `score`
- `idealCriteriaMet`
- `idealCriteriaMissing`
- `requiresExplicitAcceptance`
- `branchRelevant`
- `suitabilityRationale`
- `blockers`
- `sourceInventoryItems`

## Ranking rules

The top candidate must optimize first-run suitability in this order:

1. Public or unauthenticated access.
2. Read-only behavior.
3. One visible surface.
4. Stable rendered-result evidence.
5. No credentials or privileged account requirements.
6. Low external data/setup dependency.
7. Fresh or complete source inventory.

Branch relevance and product priority may break ties only after suitability
signals are equivalent. They must not push a credential-heavy, write-heavy, or
multi-step candidate above a trivial public candidate.

## No ideal candidate rule

When no candidate satisfies all ideal criteria:

- Recommend the lowest-risk existing candidate only if at least one candidate is
  runnable enough to demonstrate value.
- Set `explicitAcceptanceRequired: true`.
- Populate `idealCriteriaMissing`.
- Explain the risk before execution.

If every candidate is blocked by unresolved credentials, destructive behavior,
missing target, or missing source traceability, return `status: blocked`.

## Secret safety

The recommendation may include aliases, routes, branch names, file paths, and
ordinary commit identifiers. It must not include credential values, auth tokens,
cookie values, browser storage values, or secret-bearing URLs.
