# Quickstart: Golden Path Onboarding

## Prerequisites

- Install the package in editable mode if needed.
- Run commands from the repository root.
- Use the fake Core fixture for deterministic contract/integration tests.
- Do not read local env files or secret-bearing files while creating fixtures.

## Focused verification flow

1. Run first-run suitability contract tests:

   ```bash
   .venv/bin/pytest tests/contract/test_first_run_suitability_contract.py -q
   ```

2. Run missing-understanding onboarding tests:

   ```bash
   .venv/bin/pytest tests/integration/test_golden_path_onboarding_prepare.py -q
   ```

3. Run integration install guidance tests:

   ```bash
   .venv/bin/pytest tests/contract/test_integration_onboarding_guidance_contract.py tests/integration/test_integration_onboarding_guidance.py -q
   ```

4. Run guided first-run flow tests:

   ```bash
   .venv/bin/pytest tests/contract/test_guided_first_run_flow_contract.py tests/integration/test_guided_first_run_flow.py -q
   ```

5. Run understanding persistence and secret-safety regressions:

   ```bash
   .venv/bin/pytest tests/unit/test_workflow_secret_safety.py tests/unit/test_coverage_inventory_onboarding.py tests/integration/test_understanding_onboarding.py -q
   ```

6. Run adjacent Golden Path regressions from feature 009:

   ```bash
   .venv/bin/pytest tests/contract/test_first_run_recommendation_contract.py tests/contract/test_golden_path_workspace_state_contract.py tests/integration/test_golden_path_first_run.py tests/integration/test_golden_path_repair.py tests/integration/test_golden_path_workspace_state.py -q
   ```

7. Run Golden Path onboarding performance checks:

   ```bash
   .venv/bin/pytest tests/integration/test_golden_path_onboarding_performance.py -q
   ```

   Expected thresholds:

   - first-run recommendation with available inventory: under 1 second
   - install guidance rendering: under 100ms
   - clean-repository specify onboarding: under 3 minutes when safe local
     inspection is allowed

8. Run the full suite before finishing implementation:

   ```bash
   .venv/bin/pytest -q
   git diff --check
   ```

## Manual dogfood scenario

Use a sample target repository with:

- at least one trivial public read-only page
- at least one active-branch authenticated or setup-heavy feature
- no existing `.verifysignal/product-context.yaml`

Expected behavior:

1. `/verifysignal-specify` explains safe understanding preparation and proceeds
   without asking the user to manually restart.
2. First-run recommendation chooses the trivial public page.
3. The branch-relevant feature remains visible as a secondary recommendation.
4. Accepting the recommendation starts guided authoring, validation, run, safe
   repair when needed, and final result.
5. Install guidance and stage cards are visually scannable and have plain-text
   fallback.

Record the dogfood result in `docs/release-readiness.md` using the 010 scoring
template:

- whether the session reached recommendation with no more than one approval
- whether the participant could identify stage, status, next action, and safety
  boundary within 30 seconds
- whether the participant rated the first-run onboarding as clear and
  confidence-building
- whether the 80% SC-008 threshold is met, not met, or still pending
