# Contract: Golden Path Run Result

## Purpose

Define how the first golden-path run is classified and surfaced to users.

## Status values

- `not-started`: Candidate has not been accepted or run.
- `skipped`: User declined the recommended first-run candidate.
- `running`: Accepted first-run candidate is executing.
- `passed`: Core/browser passed and Spec coverage is complete without repair.
- `repairing`: A repairable failure is being classified or fixed.
- `repaired-passed`: Repair was applied, revalidated, rerun, and the final run
  reached strict pass.
- `failed`: Final run failed or repair could not reach strict pass.
- `blocked`: Missing target, incompatible Core, unresolved credential, malformed
  artifact, or another prerequisite prevents execution.
- `incomplete`: Core passed but required Spec evidence is missing.

## Strict pass criteria

`passed` and `repaired-passed` require:

- `coreBrowserStatus: passed`
- `specCoverageStatus: complete`
- `missingRequiredGates: []`
- all required gates mapped to rendered-result evidence
- project-local run artifacts written under `.verifysignal/`
- next action shown
- repair feedback recorded when repair occurred

## Result shape

First-run run and repair summaries should include:

- `firstRunStatus`
- `strictPass`
- `coreBrowserStatus`
- `specCoverageStatus`
- `selectedCandidate`
- `runOutcomeSummary`
- `repairFeedback`
- `stageCards`
- `nextAction`

Existing `status`, `coreStatus`, `coverageStatus`, `coreBrowserStatus`, and
`specCoverageStatus` fields remain compatibility contracts and must not be
silently narrowed.

## Interpretation rules

- `skipped` is not success, failure, or inconclusive.
- `incomplete` is not success even if Core/browser passed.
- Failed Core/browser execution may include diagnostic partial coverage, but
  diagnostic coverage must not be summarized as a pass.
- A repaired first run is successful only after revalidation and rerun produce
  strict pass.
