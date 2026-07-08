# Contract: Guided First-Run Flow

## Purpose

Define what happens after the user accepts the recommended Golden Path first
run. Acceptance starts a guided flow, not just a recorded alias.

## CLI surface

```text
verifysignal-spec workflow accept-first-run <alias> --project <path> --json
verifysignal-spec workflow skip-first-run --project <path> --json
verifysignal-spec workflow inspect-golden-path-state --project <path> --json
```

Existing workflow, validate, run, and repair commands continue to execute the
underlying stages. The accepted Golden Path state records the current stage and
resume action.

`accept-first-run` must not be a dead-end state setter. Its response and
subsequent resume actions must guide the user to the next existing command that
advances the accepted first run.

## JSON shape

`schemaVersion`: `verifysignal-spec-guided-first-run/v1`

Required fields:

- `status`: `accepted`, `running`, `passed`, `repaired-passed`, `blocked`,
  `failed`, or `skipped`.
- `selectedCandidate`: Accepted alias when present.
- `stage`: Current guided-flow stage.
- `resumeCommand`: Next command or agent action.
- `blocker`: Blocker object or null.
- `ownedArtifacts`: Artifacts created or updated by the guided flow.
- `stageCards`: Chat-first cards for the current stage.
- `nextAction`: Immediate next action.

`blocker` must include:

- `category`
- `stage`
- `summary`
- `requiredUserAction`
- `resumeCommand`

## Guided stages

Allowed stages:

- `recommended`
- `accepted`
- `authoring`
- `validating`
- `running`
- `repairing`
- `passed`
- `repaired-passed`
- `failed`
- `blocked`
- `skipped`

## Flow rules

- Accepting a candidate starts the guided flow and records stage `accepted`.
- The flow must progress through authoring, validation, execution, safe repair
  when needed, and final outcome reporting.
- Existing commands advance the guided state:
  - authoring/artifact creation records `authoring` and then `validating` once
    run request and skill artifacts are ready.
  - validation/runtime readiness records `validating` and either advances toward
    `running` or records a blocker with required user action.
  - browser execution records `running` and final `passed`/`failed` status.
  - safe repair records `repairing` and only records `repaired-passed` after
    repair, revalidation, rerun, and strict pass.
- The flow pauses only for required runtime data, host permissions, sensitive
  access boundaries, or incompatible Core/workspace state.
- A paused flow must include the blocked stage, required user action, and resume
  command.
- A repaired pass counts as first-run success only after repair, revalidation,
  rerun, and strict pass.
- Skipping the recommendation is not success, failure, or incomplete.

## Compatibility

The normal use-case workflow remains available after the first run. Golden Path
state applies only to the accepted first run and must not alter unrelated use
cases, run requests, skills, or run histories.
