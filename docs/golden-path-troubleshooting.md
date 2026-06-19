# Golden Path Troubleshooting

Golden Path recovery should explain the blocker, show the strongest safe
evidence, and provide the exact next action without weakening validation intent.

## Common Blockers

- Missing understanding: run safe repository understanding from the
  auto-prepare metadata and resume the original specify flow. Do not ask the
  user to restart manually unless the host cannot continue.
- Partial inventory: continue understanding with `--scope continue` or a focused
  scope, and keep the partial reason visible in recommendation output.
- Explicit acceptance required: no candidate met all ideal first-run criteria.
  Explain the missing criteria and proceed only after the user accepts the risk.
- Missing target: confirm a real browser target in clarify before planning or
  running.
- Unreachable target: start the app or correct the target URL, then rerun the
  first-run recommendation.
- Unresolved credentials: use runtime credential references; never persist
  credential values.
- Stale inventory or guidance: rerun repository understanding or regenerate the
  agent integration.
- Managed runtime blocked: run `proofsignal init --here --integration codex` to
  complete email-token unlock and managed runtime acquisition. Use `proofsignal
  core setup --core-cmd <path>` only for diagnostics, offline environments, and
  development overrides.
- Incompatible Core: verify `proofsignal core version --json` and upgrade the
  component that is behind the public CLI JSON contract.
- Install guidance missing or stale: rerun `proofsignal-spec integration install
  <codex|claude>` or `proofsignal-spec integration upgrade` to regenerate local
  onboarding guidance.
- Blocked guided flow: inspect `.proofsignal/workflows/golden-path-state.yaml`
  and follow `resumeCommand`; do not infer a new stage from chat history.
- 009 workspace state compatibility: inspect/reset state through the public
  workflow commands below. Do not delete unrelated `.proofsignal/` artifacts.
- Write rerun blocked by resource identity: validate the use case, then repair
  or re-implement the generated identity input/template, `resourceIdentity`, or
  `rerunPolicy`. Do not hand-edit `lastRun` or registry state to bypass a
  write-safety guard.
- Reviewed false-positive write outcome: record an auditable review with
  `proofsignal workflow supersede-write-outcome`; do not hand-edit managed
  run history. Write policies should use `sideEffectPolicy.allowed[]` and
  `sideEffectPolicy.forbidden[]`, not legacy
  `sideEffectPolicy.rules[].effect/match`, and confirmation signals must be
  runtime-supported confirmation signals.
- Generated identity collision: the refreshed value repeated a locally recorded
  committed binding for the same use case and target. Adjust the generation
  strategy or owner-approved seed before rerunning; no live target probe is
  required by default.

## Workspace State

Use read-only inspection before cleanup:

```sh
proofsignal workflow inspect-golden-path-state --json
proofsignal workflow reset-golden-path-state --preview --json
proofsignal workflow reset-golden-path-state --confirm --json
```

Reset removes only Golden Path-owned state and preserves unrelated use cases,
run requests, skills, reports, repair sessions, registry records, and
user-authored files.

## Outcome Meanings

- `passed`: direct strict pass; first-run success.
- `repaired-passed`: safe repair, revalidation, rerun, and strict pass; also
  first-run success.
- `skipped`: the user declined Golden Path; manual selection continues.
- `blocked`: required runtime data, host permission, safety boundary, or runtime
  compatibility stopped automatic continuation.
- `failed` or `incomplete`: the first run did not prove all required gates; use
  repair or replan with clear product feedback.
