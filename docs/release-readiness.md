# Release Readiness

This checklist defines what must be true before the Golden Path is ready to
demo or ready to release.

## Ready To Demo

- A new user can see one strongly recommended first-run candidate for a real
  target.
- The user can accept or skip the recommendation with clear semantics.
- A successful first run reports strict pass, or repaired-passed after safe
  mechanical repair, with stage-card evidence.
- Common blockers provide an exact next action instead of suggesting fake/demo
  fallbacks.
- Workflow output uses clear pass/fail language and distinguishes skipped,
  blocked, incomplete, failed, passed, and repaired-passed.

## Ready To Release

- Public CLI JSON contracts are covered by contract tests.
- Workspace state inspect/reset preserves unrelated `.proofsignal/` artifacts.
- Repair autonomy preserves required gates and requires confirmation for intent
  changes.
- Documentation explains Golden Path, troubleshooting, examples, and release
  checks.
- Focused tests and the full regression suite pass locally.

## Pass/Fail Checklist

- Documentation: Golden Path, troubleshooting, examples, and release readiness
  are linked from the README.
- Examples: public unauthenticated, authenticated secret-safe, repairable
  failure, and conditional data examples are covered.
- Workflow output: recommendation, acceptance, run, repair, blockers, and final
  result can be rendered as stage cards.
- Troubleshooting: missing target, unreachable target, stale state, credentials,
  and Core compatibility have recovery actions.
- Secret safety: no credential values, browser storage, cookies, or raw
  sensitive payloads are persisted or documented.
- Core compatibility: Core access stays behind public CLI JSON operations.
- Regression coverage: focused tests and the full suite pass before release.
