# Release Readiness

This checklist defines what must be true before the Golden Path is ready to
demo or ready to release.

## Ready To Demo

- A new user can see one strongly recommended first-run candidate for a real
  target.
- The recommended first run is the simplest reliable existing behavior, not the
  most branch-relevant or highest-priority complex flow.
- The user can accept or skip the recommendation with clear semantics.
- A successful first run reports strict pass, or repaired-passed after safe
  mechanical repair, with stage-card evidence.
- Missing understanding is auto-prepared when safe and resumes recommendation
  without manual restart.
- Integration install prints next steps and writes local onboarding guidance.
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

## 010 Golden Path Onboarding Acceptance

- First-run recommendation completes in under 1 second when inventory is
  available.
- Integration onboarding guidance rendering completes in under 100ms.
- Clean-repository specify onboarding reaches first-run recommendation in under
  3 minutes when safe local inspection is allowed.
- At least 80% of moderated dogfood participants can identify the current
  stage, status, next action, and safety boundary within 30 seconds.

## Moderated Dogfood Script

1. Start from a representative repository with no `.proofsignal/product-context.yaml`.
2. Install Codex or Claude integration.
3. Ask the participant what the next command is and what sensitive boundaries
   apply.
4. Run `/proofsignal-specify` and observe whether safe understanding prepares
   and resumes without manual restart.
5. Confirm the recommended first run is public/read-only/simple when such a
   candidate exists.
6. Accept the recommendation and follow authoring, validation, run, safe repair
   if needed, and final outcome.

## Result Recording Template

- Repository:
- Integration:
- Date:
- Participant:
- Approvals required before recommendation:
- Recommended alias:
- Branch-relevant aliases listed separately:
- Final outcome: `passed` / `repaired-passed` / `skipped` / `blocked` / `failed`
- Could identify stage/status/next action/safety in 30 seconds: yes/no
- Confidence-building rating: 1-5
- SC-008 threshold: met / not met / pending

## Current Dogfood Status

SC-008 moderated dogfood result is pending. Automated focused tests cover the
010 contracts, but a maintainer dogfood session still needs to be recorded using
the template above before release signoff.
