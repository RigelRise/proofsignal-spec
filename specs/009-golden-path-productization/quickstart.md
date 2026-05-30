# Quickstart: Golden Path Productization

This guide verifies the planned feature without relying on private ProofSignal
Core internals.

## 1. Verify local package version

```bash
PYTHONPATH=src python3 -m proofsignal_spec --version
```

Expected: the local package version is used. If a globally installed
`proofsignal-spec` is older, use `PYTHONPATH=src python3 -m proofsignal_spec`
for development checks or reinstall the local package.

## 2. Run focused tests during implementation

Planned focused tests:

```bash
.venv/bin/pytest tests/unit/test_first_run_recommendation.py
.venv/bin/pytest tests/unit/test_first_run_performance.py
.venv/bin/pytest tests/contract/test_first_run_recommendation_contract.py
.venv/bin/pytest tests/contract/test_agent_chat_stage_card_contract.py
.venv/bin/pytest tests/contract/test_golden_path_run_result_contract.py
.venv/bin/pytest tests/contract/test_golden_path_workspace_state_contract.py
.venv/bin/pytest tests/contract/test_repair_autonomy_contract.py
.venv/bin/pytest tests/contract/test_golden_path_examples_contract.py
.venv/bin/pytest tests/contract/test_golden_path_troubleshooting_contract.py
.venv/bin/pytest tests/contract/test_golden_path_readiness_contract.py
.venv/bin/pytest tests/integration/test_golden_path_examples.py
.venv/bin/pytest tests/integration/test_golden_path_troubleshooting.py
.venv/bin/pytest tests/integration/test_golden_path_workspace_state.py
.venv/bin/pytest tests/integration/test_golden_path_readiness.py
```

## 3. Verify existing workflow regressions

```bash
.venv/bin/pytest tests/contract/test_cli_run_contract.py
.venv/bin/pytest tests/contract/test_cli_repair_contract.py
.venv/bin/pytest tests/integration/test_workflow_coverage_inventory.py
.venv/bin/pytest tests/integration/test_workflow_run.py
.venv/bin/pytest tests/integration/test_workflow_repair.py
```

## 4. Verify Core public boundary

Use the configured public Core command only:

```bash
PROOFSIGNAL_CORE_CMD=/path/to/proofsignal \
  PYTHONPATH=src python3 -m proofsignal_spec core version --json
```

Expected: output uses the public Core version schema. Do not import private Core
packages or inspect undocumented report internals.

## 5. Verify first-run recommendation behavior

After implementation, initialize or prepare a target workspace with safe
coverage inventory and a confirmed real target:

```bash
PYTHONPATH=src python3 -m proofsignal_spec workflow recommend-first-run --project <target-project> --json
```

Expected:

- `schemaVersion` is `proofsignal-spec-first-run-recommendation/v1`.
- `status` is `ready` when a first-run candidate exists.
- The top candidate includes ranking rationale and a strong acceptance prompt.
- The output includes an agent-chat stage card.
- Missing target or unresolved credentials produce `blocked`, not a fake/demo
  fallback.

## 6. Verify chat stage-card guidance

Regenerate Codex and Claude integrations in a temporary project and inspect the
generated guidance:

```bash
PYTHONPATH=src python3 -m proofsignal_spec init <tmp-project> --integration codex --json
PYTHONPATH=src python3 -m proofsignal_spec integration install claude --project <tmp-project> --json
```

Expected generated guidance describes the required stage-card fields:
title, status marker, one-line summary, why it matters, primary evidence,
repair/change details when present, and next action.

## 7. Verify repair autonomy

Use deterministic fake Core fixtures only for regression tests. Confirm that
safe mechanical selector/wait/ordering repairs can be classified as
auto-applicable when intent is preserved, while data, credential, gate, and
expected-behavior changes require confirmation or block.

## 8. Verify canonical example coverage

Use deterministic fixtures or temporary workspaces to verify all four canonical
examples:

```bash
.venv/bin/pytest tests/contract/test_golden_path_examples_contract.py
.venv/bin/pytest tests/integration/test_golden_path_examples.py
```

Expected:

- Public unauthenticated example has repeatable pass coverage.
- Authenticated example uses secret-safe credential references or dummy values.
- Repairable failure example reaches a classified failure and explicit rerun
  path.
- Conditional or data-dependent example reports pass, fail, blocked, or
  not-evaluated semantics clearly.

## 9. Verify Golden Path Workspace State inspect/reset

Prepare a temporary target project with golden-path state and unrelated
`.proofsignal/` artifacts:

```bash
PYTHONPATH=src python3 -m proofsignal_spec workflow inspect-golden-path-state --project <target-project> --json
PYTHONPATH=src python3 -m proofsignal_spec workflow reset-golden-path-state --project <target-project> --preview --json
PYTHONPATH=src python3 -m proofsignal_spec workflow reset-golden-path-state --project <target-project> --confirm --json
```

Expected:

- Inspect is read-only and reports first-run status, owned artifacts, preserved
  artifacts, warnings, resume hint, and next action.
- Preview reports the reset plan without modifying files.
- Confirmed reset touches only golden-path-owned state and preserves unrelated
  use cases, run requests, reusable skills, reports, repair sessions, registry
  records, and user-authored files.

## 10. Verify release-readiness definitions

```bash
.venv/bin/pytest tests/contract/test_golden_path_readiness_contract.py
.venv/bin/pytest tests/integration/test_golden_path_readiness.py
```

Expected: the readiness checklist defines separate `ready to demo` and
`ready to release` outcomes and returns a clear pass/fail result for every item.

Ready to demo means the first-run recommendation, accept/skip decision, stage
cards, strict pass or repaired-passed result, and common blocker recovery are
demonstrable.

Ready to release means documentation, examples, workflow output,
troubleshooting, secret safety, Core compatibility, and regression coverage all
pass their focused checks.

## 11. Run full regression suite

```bash
.venv/bin/pytest -q
```

Expected: all existing tests pass plus the new first-run productization tests.

## Implementation Verification

Recorded during implementation:

- Focused Golden Path tests passed:
  `.venv/bin/pytest tests/unit/test_first_run_recommendation.py tests/unit/test_first_run_performance.py tests/contract/test_first_run_recommendation_contract.py tests/contract/test_agent_chat_stage_card_contract.py tests/contract/test_golden_path_run_result_contract.py tests/contract/test_golden_path_workspace_state_contract.py tests/contract/test_repair_autonomy_contract.py tests/contract/test_golden_path_examples_contract.py tests/contract/test_golden_path_troubleshooting_contract.py tests/contract/test_golden_path_readiness_contract.py tests/integration/test_golden_path_examples.py tests/integration/test_golden_path_troubleshooting.py tests/integration/test_golden_path_workspace_state.py tests/integration/test_golden_path_readiness.py`
- Adjacent workflow regressions passed:
  `.venv/bin/pytest tests/contract/test_cli_run_contract.py tests/contract/test_cli_repair_contract.py tests/integration/test_workflow_coverage_inventory.py tests/integration/test_workflow_run.py tests/integration/test_workflow_repair.py`
- Full suite passed: `.venv/bin/pytest -q`.
- Deviations: none.
