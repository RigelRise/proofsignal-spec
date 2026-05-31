# Tasks: Golden Path Onboarding

**Input**: Design documents from `specs/010-golden-path-onboarding/`  
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`

**Tests**: Required by the project constitution and delivery guardrails for public CLI contracts, workspace schema behavior, Core compatibility, secret safety, cross-agent portability, performance, and UX criteria. Write or update focused tests first and confirm the expected red failure before implementation.

**Organization**: Tasks are grouped by user story so each story can be implemented and validated independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks.
- **[Story]**: User story label for story phases only.
- Every task includes exact file paths.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared fixtures and documentation references for the onboarding refinements.

- [X] T001 Update the active feature reference and planning notes in AGENTS.md to point at specs/010-golden-path-onboarding/plan.md
- [X] T002 [P] Add shared fixture builders for onboarding repositories, candidates, and product context in tests/fixtures/workflows/golden_path_onboarding.py
- [X] T003 Add shared assertion helpers for stage cards, onboarding guidance, and public-metadata secret safety in tests/fixtures/workflows/golden_path_onboarding.py
- [X] T004 [P] Add quickstart command expectations for the new focused test files in specs/010-golden-path-onboarding/quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add shared schema/model primitives that every user story depends on.

**CRITICAL**: No user story implementation should start until these shared model and fixture contracts exist.

- [X] T005 [P] Add failing model contract tests for FirstRunSuitabilityScore, FirstRunIdealCriteria, GuidedFirstRunState, OnboardingGuidance, and UnderstandingOnboardingResult in tests/contract/test_golden_path_onboarding_models_contract.py
- [X] T006 [P] Add failing serialization/unit tests for the same shared onboarding models in tests/unit/test_golden_path_onboarding_models.py
- [X] T007 Add shared dataclasses and schema constants for first-run suitability, ideal criteria, guided flow state, onboarding guidance, and understanding onboarding result in src/proofsignal_spec/workflows/models.py
- [X] T008 Add to_dict/from_dict validation coverage for new onboarding models in src/proofsignal_spec/workflows/models.py
- [X] T009 Run the focused shared model tests from tests/contract/test_golden_path_onboarding_models_contract.py and tests/unit/test_golden_path_onboarding_models.py and confirm they pass

**Checkpoint**: Shared onboarding data contracts are available for all stories.

---

## Phase 3: User Story 1 - Product-Owned First-Run Recommendation (Priority: P1) MVP

**Goal**: Recommend the simplest reliable first run, keep branch-relevant candidates separate, require explicit acceptance when no ideal candidate exists, and guide accepted first runs through outcome reporting.

**Independent Test**: In a fixture repository with one public read-only candidate and one authenticated active-branch candidate, `recommend-first-run` ranks the public candidate first; accepting it records a guided end-to-end flow state with resume action and stage cards.

### Tests for User Story 1

- [X] T010 [P] [US1] Add failing contract tests for first-run suitability JSON fields, ideal criteria, branchRelevantCandidates, and explicitAcceptanceRequired in tests/contract/test_first_run_suitability_contract.py
- [X] T011 [P] [US1] Add failing unit tests for suitability scoring that demotes auth/write/setup-heavy candidates below public read-only rendered flows in tests/unit/test_first_run_suitability.py
- [X] T012 [US1] Add failing unit tests for no-ideal-candidate behavior requiring idealCriteriaMissing and explicit acceptance in tests/unit/test_first_run_suitability.py
- [X] T013 [P] [US1] Add failing integration tests for recommend-first-run choosing the trivial public candidate while listing active-branch candidates separately in tests/integration/test_first_run_suitability.py
- [X] T014 [P] [US1] Add failing contract tests for guided first-run accept/skip/state fields, manual selection after skip, and resume semantics in tests/contract/test_guided_first_run_flow_contract.py
- [X] T015 [P] [US1] Add failing integration tests for accept-first-run recording guided stage accepted, resumeCommand, and stageCards while skip preserves ordinary manual use-case selection in tests/integration/test_guided_first_run_flow.py
- [X] T016 [US1] Add failing integration tests for accepted first-run end-to-end progression through authoring, validating, running, safe repair, repaired-passed/direct-passed final outcome, stageCards, resumeCommand, and strictPass preservation in tests/integration/test_guided_first_run_flow.py

### Implementation for User Story 1

- [X] T017 [US1] Implement ideal criteria evaluation and suitability scoring fields in src/proofsignal_spec/workflows/first_run.py
- [X] T018 [US1] Add branch-relevance detection and branchRelevantCandidates output without allowing branch relevance to outrank lower-risk candidates in src/proofsignal_spec/workflows/first_run.py
- [X] T019 [US1] Implement no-ideal-candidate fallback with idealCriteriaMissing, requiresExplicitAcceptance, and explicitAcceptanceRequired in src/proofsignal_spec/workflows/first_run.py
- [X] T020 [US1] Extend FirstRunRecommendation model output for idealCriteria, branchRelevantCandidates, and explicitAcceptanceRequired in src/proofsignal_spec/workflows/models.py
- [X] T021 [US1] Update recommendation stage-card content to explain unmet ideal criteria and secondary branch-relevant candidates in src/proofsignal_spec/workflows/stage_cards.py
- [X] T022 [US1] Implement GuidedFirstRunState persistence transitions for accepted, skipped, authoring, validating, running, repairing, passed, repaired-passed, failed, and blocked in src/proofsignal_spec/workflows/first_run.py
- [X] T023 [US1] Update accept-first-run and skip-first-run command handlers to return guided first-run schema, stage, resumeCommand, and stageCards in src/proofsignal_spec/commands/workflow.py
- [X] T024 [US1] Update CLI workflow dispatch and text output for guided first-run accept/skip/recommend responses in src/proofsignal_spec/cli.py
- [X] T025 [US1] Update author, validate, run, and repair state integration so accepted first-run stages and strictPass/repaired-passed results write guided-flow state in src/proofsignal_spec/commands/author.py, src/proofsignal_spec/commands/validate.py, src/proofsignal_spec/commands/run.py, and src/proofsignal_spec/commands/repair.py
- [X] T026 [US1] Run focused US1 tests from tests/contract/test_first_run_suitability_contract.py, tests/unit/test_first_run_suitability.py, tests/contract/test_guided_first_run_flow_contract.py, and tests/integration/test_guided_first_run_flow.py

**Checkpoint**: User Story 1 is independently functional and demonstrable as the MVP.

---

## Phase 4: User Story 2 - Smooth Missing-Understanding Onboarding (Priority: P2)

**Goal**: When specify starts without repository understanding, safely prepare understanding automatically when possible and return to first-run recommendation without requiring command restart.

**Independent Test**: In a clean target repository with no product context, the specify prerequisite path reports safe auto-preparation/resume behavior and reaches first-run recommendation with no manual restart in allowed scenarios.

### Tests for User Story 2

- [X] T027 [P] [US2] Add failing contract tests for missing-understanding auto-prepare guidance and resume fields in tests/contract/test_understanding_onboarding_contract.py
- [X] T028 [P] [US2] Add failing integration tests for clean-repository specify onboarding that prepares safe understanding and resumes recommendation in tests/integration/test_golden_path_onboarding_prepare.py
- [X] T029 [US2] Add failing integration tests for host-permission or sensitive-boundary blockers that ask once and provide resume action in tests/integration/test_golden_path_onboarding_prepare.py
- [X] T030 [P] [US2] Add failing template tests requiring /proofsignal-specify and /proofsignal-understand guidance to describe auto-prepare and no manual restart in tests/integration/test_agent_template_preservation.py

### Implementation for User Story 2

- [X] T031 [US2] Add onboarding preparation result builder and resume metadata in src/proofsignal_spec/workflows/first_run.py
- [X] T032 [US2] Update workflow prerequisite checks for specify to classify missing understanding as auto-preparable when safe and as approval-required only for host/sensitive boundaries in src/proofsignal_spec/workflows/prerequisites.py
- [X] T033 [US2] Update workflow check output to include preparation status, resumeCommand, and stageCards for missing-understanding onboarding in src/proofsignal_spec/commands/workflow.py
- [X] T034 [US2] Update /proofsignal-specify and /proofsignal-understand command templates to auto-prepare safe understanding and resume first-run recommendation in src/proofsignal_spec/templates/agent-commands/proofsignal.specify.md and src/proofsignal_spec/templates/agent-commands/proofsignal.understand.md
- [X] T035 [US2] Update Codex and Claude generated skill guidance for missing-understanding auto-prepare behavior in src/proofsignal_spec/integrations/codex.py and src/proofsignal_spec/integrations/claude.py
- [X] T036 [US2] Run focused US2 tests from tests/contract/test_understanding_onboarding_contract.py, tests/integration/test_golden_path_onboarding_prepare.py, and tests/integration/test_agent_template_preservation.py

**Checkpoint**: User Story 2 works independently on clean repositories and does not regress ordinary specify behavior.

---

## Phase 5: User Story 3 - Clear Integration Install Guidance (Priority: P3)

**Goal**: Integration install produces rich terminal next steps and durable local guidance that explain Golden Path, safety boundaries, success/repair semantics, and fallback readable formatting.

**Independent Test**: Installing Codex or Claude integration returns onboardingGuide JSON, prints scannable terminal guidance, and writes local guide content with equivalent plain-text semantics.

### Tests for User Story 3

- [X] T037 [P] [US3] Add failing contract tests for integration install onboardingGuide JSON fields in tests/contract/test_integration_onboarding_guidance_contract.py
- [X] T038 [P] [US3] Add failing integration tests for Codex install terminal output and generated local guide in tests/integration/test_integration_onboarding_guidance.py
- [X] T039 [US3] Add failing integration tests for Claude install terminal output and generated local guide in tests/integration/test_integration_onboarding_guidance.py
- [X] T040 [P] [US3] Add failing unit tests for plain-text fallback and no-secret rendering in tests/unit/test_integration_onboarding_guidance.py

### Implementation for User Story 3

- [X] T041 [US3] Implement onboarding guidance data builder with terminal summary, stage markers, safety boundaries, success semantics, and plainTextFallback in src/proofsignal_spec/integrations/base.py
- [X] T042 [US3] Update integration install and upgrade command results to include onboardingGuide in src/proofsignal_spec/commands/integration.py
- [X] T043 [US3] Update CLI text emission for integration install/upgrade to render visually scannable sections, status markers, colors when available, and plain-text fallback in src/proofsignal_spec/cli.py
- [X] T044 [US3] Add generated local onboarding guide file for Codex integration in src/proofsignal_spec/integrations/codex.py
- [X] T045 [US3] Add generated local onboarding guide file for Claude integration in src/proofsignal_spec/integrations/claude.py
- [X] T046 [US3] Add shared guidance copy constants for Golden Path next steps, safety boundaries, success, repaired-pass, skip, blocked, and failed semantics in src/proofsignal_spec/templates/agent_guidance.py
- [X] T047 [US3] Run focused US3 tests from tests/contract/test_integration_onboarding_guidance_contract.py, tests/integration/test_integration_onboarding_guidance.py, and tests/unit/test_integration_onboarding_guidance.py

**Checkpoint**: User Story 3 is independently demonstrable by installing either integration in a temporary repository.

---

## Phase 6: User Story 4 - Reliable Understanding Persistence (Priority: P4)

**Goal**: Understanding persistence completes or clearly labels inventory, normalizes source traceability where safe, allows public metadata such as commit hashes, and emits actionable schema guidance instead of trial-and-error blockers.

**Independent Test**: Persisting a representative understanding payload with git metadata and candidate surfaces succeeds on the first valid attempt, normalizes sourceInventoryItems when inferable, and blocks missing traceability with user-readable guidance.

### Tests for User Story 4

- [X] T048 [US4] Add failing contract tests for understanding-onboarding persistence fields, partial labels, and source traceability blockers in tests/contract/test_understanding_onboarding_contract.py
- [X] T049 [P] [US4] Add failing unit tests that normal commit hashes, branch names, route paths, file paths, inventory IDs, and candidate aliases are not secret-looking values in tests/unit/test_workflow_secret_safety.py
- [X] T050 [P] [US4] Add failing unit tests for candidate sourceInventoryItems normalization from inventory paths and surfaces in tests/unit/test_coverage_inventory_onboarding.py
- [X] T051 [P] [US4] Add failing integration tests for understand/persist completing representative inventory on first valid attempt, including trivial public read-only routes before authenticated active-branch flows, in tests/integration/test_understanding_onboarding.py
- [X] T052 [US4] Add failing integration tests for partial inventory labeling and user-readable invalid-payload blockers in tests/integration/test_understanding_onboarding.py

### Implementation for User Story 4

- [X] T053 [US4] Update secret-safety allowlist for public metadata fields and normal commit identifiers in src/proofsignal_spec/workspace/validation.py
- [X] T054 [US4] Improve coverage inventory normalization to infer sourceInventoryItems from candidate surface, route, path, source refs, and inventory item IDs in src/proofsignal_spec/workflows/coverage_inventory.py
- [X] T055 [US4] Add partialInventoryReasons and sourceTraceabilityStatus normalization to understanding persistence in src/proofsignal_spec/workflows/stage_persistence.py
- [X] T056 [US4] Improve persist understand blocker messages to name missing candidate traceability and recovery guidance in src/proofsignal_spec/workflows/stage_persistence.py
- [X] T057 [US4] Ensure first-run recommendation labels partial or stale inventory using existing understanding freshness rules in src/proofsignal_spec/workflows/first_run.py
- [X] T058 [US4] Update understanding markdown generation to report complete, partial, stale, and normalized traceability status in src/proofsignal_spec/workflows/stage_documents.py
- [X] T059 [US4] Update /proofsignal-understand command guidance to attempt the full discoverable use-case inventory, enumerate trivial public/read-only candidates before branch-heavy flows, and label partial inventory in src/proofsignal_spec/templates/agent-commands/proofsignal.understand.md
- [X] T060 [US4] Run focused US4 tests from tests/contract/test_understanding_onboarding_contract.py, tests/unit/test_workflow_secret_safety.py, tests/unit/test_coverage_inventory_onboarding.py, and tests/integration/test_understanding_onboarding.py

**Checkpoint**: User Story 4 is independently functional and removes schema-trial friction from understanding persistence.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate compatibility, documentation, versioning, and full regression safety.

- [X] T061 [P] Update README Golden Path onboarding docs and install guidance examples in README.md
- [X] T062 [P] Update docs/golden-path.md with first-run-only scope, suitability ranking, no-ideal-candidate behavior, guided accept flow, and manual use-case selection after skip
- [X] T063 [P] Update docs/golden-path-troubleshooting.md with missing understanding, partial inventory, explicit acceptance, install guidance, blocked guided-flow recovery cases, and 009 state compatibility recovery
- [X] T064 [P] Update docs/release-readiness.md with 010 onboarding acceptance criteria, moderated dogfood script, scoring rubric, performance checks, and a result-recording template
- [X] T065 Add failing compatibility tests for existing 009 golden-path workspace state inspection/reset/recommend behavior with the new guided state fields in tests/contract/test_golden_path_workspace_state_contract.py and tests/integration/test_golden_path_workspace_state.py
- [X] T066 Add performance validation tests for first-run recommendation under 1 second with available inventory, install guidance rendering under 100ms, and clean-repository onboarding timing assumptions in tests/integration/test_golden_path_onboarding_performance.py
- [ ] T067 Run the moderated dogfood validation checklist from docs/release-readiness.md against a representative target repository or maintainer dogfood session and record whether SC-008 is met in docs/release-readiness.md
- [X] T068 Run adjacent Golden Path regression tests from tests/contract/test_first_run_recommendation_contract.py, tests/integration/test_golden_path_first_run.py, tests/integration/test_golden_path_repair.py, and tests/integration/test_golden_path_workspace_state.py
- [X] T069 Run workflow/template regression tests from tests/integration/test_workflow_agent_public_guidance.py, tests/integration/test_agent_template_preservation.py, and tests/contract/test_agent_chat_stage_card_contract.py
- [X] T070 Run full test suite with .venv/bin/pytest -q
- [X] T071 Run git diff --check in the proofsignal-spec repository
- [X] T072 Evaluate version impact in pyproject.toml and src/proofsignal_spec/__init__.py and apply a patch/minor bump if required by the completed behavior

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1; blocks all user stories.
- **US1 Product-owned recommendation**: Depends on Phase 2; MVP.
- **US2 Missing-understanding onboarding**: Depends on Phase 2; can run after or alongside US1 once shared models exist.
- **US3 Integration install guidance**: Depends on Phase 2; independent of US1/US2 implementation.
- **US4 Reliable understanding persistence**: Depends on Phase 2; supports US1/US2 recommendation quality.
- **Polish**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1 (P1)**: MVP and can ship alone after Foundation.
- **US2 (P2)**: Independent after Foundation, but benefits from US1 stage-card and recommendation model fields.
- **US3 (P3)**: Independent after Foundation.
- **US4 (P4)**: Independent after Foundation, but should be complete before final release because US1 recommendation quality depends on inventory quality.

### Within Each User Story

- Tests must be written first and fail for the expected missing behavior.
- Model/contract fields before service logic.
- Service/workflow logic before CLI/template rendering.
- Focused tests before moving to the next story.

---

## Parallel Opportunities

- T002 and T004 can run in parallel; T003 follows T002 because it extends the same fixture helper file.
- T005 and T006 can run in parallel before T007/T008.
- Test tasks within each user story marked [P] can run in parallel.
- US3 integration guidance tasks can proceed independently after Foundation.
- US4 persistence tests and secret-safety tests can proceed independently after Foundation.
- Documentation polish tasks T061-T064 can run in parallel after story behavior stabilizes.
- T065 and T066 can run after story behavior stabilizes; T067 depends on T064 and should run before final release signoff.

## Parallel Example: User Story 1

```bash
# Launch US1 test authoring in parallel:
Task: "T010 contract tests in tests/contract/test_first_run_suitability_contract.py"
Task: "T011 unit tests in tests/unit/test_first_run_suitability.py"
Task: "T013 integration tests in tests/integration/test_first_run_suitability.py"
Task: "T014 contract tests in tests/contract/test_guided_first_run_flow_contract.py"
Task: "T015 integration tests in tests/integration/test_guided_first_run_flow.py"
```

## Parallel Example: User Story 3

```bash
# Launch US3 test authoring in parallel:
Task: "T037 contract tests in tests/contract/test_integration_onboarding_guidance_contract.py"
Task: "T038 Codex integration install tests in tests/integration/test_integration_onboarding_guidance.py"
Task: "T040 fallback/no-secret unit tests in tests/unit/test_integration_onboarding_guidance.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 and Phase 2.
2. Complete US1 tests and confirm red failures.
3. Implement US1 recommendation and guided accept flow.
4. Run US1 focused tests.
5. Demonstrate recommend-first-run + accept-first-run on a fixture repository.

### Incremental Delivery

1. Add US1 for deterministic first-run ranking and guided accept state.
2. Add US2 for clean-repository specify onboarding.
3. Add US3 for polished integration install guidance.
4. Add US4 for reliable understanding persistence and inventory quality.
5. Run polish, compatibility, performance, dogfood, and regression tasks and update version if needed.

### Validation Discipline

- Do not weaken existing 009 strict-pass or repair-autonomy semantics.
- Do not persist credential values or sensitive runtime values.
- Do not introduce private Core imports or undocumented report parsing.
- Keep durable project docs, generated guidance, and tasks in English.
