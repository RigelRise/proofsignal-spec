# Golden Path Troubleshooting

Golden Path recovery should explain the blocker, show the strongest safe
evidence, and provide the exact next action without weakening validation intent.

## Common Blockers

- Missing target: confirm a real browser target in clarify before planning or
  running.
- Unreachable target: start the app or correct the target URL, then rerun the
  first-run recommendation.
- Unresolved credentials: use runtime credential references; never persist
  credential values.
- Stale inventory or guidance: rerun repository understanding or regenerate the
  agent integration.
- Incompatible Core: verify `proofsignal-spec core version --json` and upgrade
  the component that is behind the public CLI JSON contract.

## Workspace State

Use read-only inspection before cleanup:

```sh
proofsignal-spec workflow inspect-golden-path-state --json
proofsignal-spec workflow reset-golden-path-state --preview --json
proofsignal-spec workflow reset-golden-path-state --confirm --json
```

Reset removes only Golden Path-owned state and preserves unrelated use cases,
run requests, skills, reports, repair sessions, registry records, and
user-authored files.
