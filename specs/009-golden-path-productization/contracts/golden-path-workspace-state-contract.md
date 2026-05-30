# Contract: Golden Path Workspace State

## Purpose

Define how users and agents inspect, resume, and reset project-local golden-path
state without damaging unrelated `.proofsignal/` artifacts.

## Proposed CLI surface

```text
proofsignal-spec workflow inspect-golden-path-state --project <path> --json
proofsignal-spec workflow reset-golden-path-state --project <path> --preview --json
proofsignal-spec workflow reset-golden-path-state --project <path> --confirm --json
```

`inspect-golden-path-state` is read-only. `reset-golden-path-state --preview`
returns the same reset plan without modifying files. `--confirm` is required for
any cleanup that removes or rewrites golden-path-owned state.

## JSON schema

`schemaVersion`: `proofsignal-spec-golden-path-workspace-state/v1`

Required fields:

- `status`: `ready`, `blocked`, `empty`, or `reset`.
- `firstRunStatus`: Current first-run status when present.
- `ownedArtifacts`: Golden-path-owned paths that may be inspected or reset.
- `preservedArtifacts`: Existing or unrelated `.proofsignal/` paths that must
  be left untouched.
- `resetPreview`: Ordered reset actions, empty when no reset is needed.
- `resumeHint`: Next safe command when the journey can resume.
- `warnings`: Recoverable warnings such as stale schemas or missing generated
  guidance.
- `nextAction`: Next CLI command or agent action.

## Preservation rules

- Inspect must never modify files.
- Reset must not remove unrelated use cases, run requests, reusable skills,
  reports, repair sessions, registry entries, or user-authored files.
- Reset must preserve credentials and must never print or persist secret-looking
  values, browser storage values, cookie values, or raw sensitive payloads.
- Reset must block instead of deleting when artifact ownership is ambiguous.
- Older workspace state must be reported as stale or incompatible with a safe
  recovery action.

## Interpretation rules

- `empty` means no golden-path state is present and reset is a no-op.
- `blocked` means the state cannot be safely reset without user clarification or
  a compatibility migration.
- `reset` means cleanup completed and unrelated artifacts were preserved.
- A reset does not count as first-run success, failure, or skip.
