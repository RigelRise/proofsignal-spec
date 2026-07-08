# Tasks: Golden Path Productization

**Input**: Design documents from `specs/009-golden-path-productization/`
**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md),
[research.md](./research.md), [data-model.md](./data-model.md),
[contracts/](./contracts/), [quickstart.md](./quickstart.md)

**Tests**: Required. This feature changes public CLI contracts, workspace state,
Core compatibility handling, generated agent guidance, repair behavior, secret
safety, and usability claims. Write focused tests first and confirm expected
failure before implementation.

**Organization**: Tasks are grouped by user story so each story can be
implemented and tested independently.

## Phase 1: Setup

**Purpose**: Prepare feature-specific fixtures and documentation locations.

- [X] T001 [P] Create golden-path workflow fixture helpers in `tests/fixtures/workflows/golden_path_productization.py`
- [X] T002 [P] Create first-run documentation skeleton in `docs/golden-path.md`
- [X] T003 [P] Create release-readiness documentation skeleton in `docs/release-readiness.md`

---

## Phase 2: Foundational

**Purpose**: Shared first-run and stage-card primitives required by all stories.

**Critical**: No user-story implementation should begin until these shared
primitives exist with failing tests.

- [X] T004 [P] Add failing unit tests for `AgentChatStageCard` validation in `tests/unit/test_stage_cards.py`
- [X] T005 [P] Add failing unit tests for first-run state primitives in `tests/unit/test_first_run_state.py`
- [X] T006 [P] Add failing performance tests for first-run candidate ranking under 1 second and stage-card generation under 100ms in `tests/unit/test_first_run_performance.py`
- [X] T007 Add first-run data primitives for recommendation and run state in `src/verifysignal_spec/workflows/models.py`
- [X] T008 Add reusable agent-chat stage-card builders in `src/verifysignal_spec/workflows/stage_cards.py`
- [X] T009 Add first-run workflow module skeleton with state helpers in `src/verifysignal_spec/workflows/first_run.py`
- [X] T010 Add secret-safe target and evidence summarization helpers for first-run output in `src/verifysignal_spec/workflows/first_run.py`

**Checkpoint**: Stage-card and first-run primitives exist and can be used by
recommendation, run, repair, and agent-template tasks.

---

## Phase 3: User Story 1 - Complete First Golden Path (Priority: P1)

**Goal**: A new user gets a strongly recommended first-run candidate on a real
target, accepts or skips it, and sees a strict pass directly or after the shared
first-run pipeline.

**Independent Test**: In a temporary target workspace with safe inventory and a
confirmed real target, `workflow recommend-first-run --json` ranks a candidate,
`workflow accept-first-run <alias> --json` records acceptance, `run <alias>
--json` reports strict pass when Core/browser and Spec coverage pass, and the
output includes agent-chat stage-card data.

### Tests for User Story 1

- [X] T011 [P] [US1] Add failing contract tests for `workflow recommend-first-run`, `workflow accept-first-run`, and `workflow skip-first-run` JSON in `tests/contract/test_first_run_recommendation_contract.py`
- [X] T012 [P] [US1] Add failing unit tests for candidate ranking signals and fake/demo target rejection in `tests/unit/test_first_run_recommendation.py`
- [X] T013 [P] [US1] Add failing contract tests for required agent-chat stage-card fields in `tests/contract/test_agent_chat_stage_card_contract.py`
- [X] T014 [P] [US1] Add failing integration tests for real-target-first recommendation and skip semantics in `tests/integration/test_golden_path_first_run.py`
- [X] T015 [P] [US1] Add failing integration tests for generated Codex and Claude stage-card guidance in `tests/integration/test_workflow_agent_public_guidance.py`

### Implementation for User Story 1

- [X] T016 [US1] Implement candidate scoring and recommendation selection in `src/verifysignal_spec/workflows/first_run.py`
- [X] T017 [US1] Implement `recommend-first-run`, `accept-first-run`, and `skip-first-run` workflow command handlers in `src/verifysignal_spec/commands/workflow.py`
- [X] T018 [US1] Add `workflow recommend-first-run`, `workflow accept-first-run`, and `workflow skip-first-run` argparse subcommands in `src/verifysignal_spec/cli.py`
- [X] T019 [US1] Persist accepted and skipped golden-path first-run state in `src/verifysignal_spec/workflows/repository.py`
- [X] T020 [US1] Include first-run status, strict-pass flag, and stage cards in run output from `src/verifysignal_spec/commands/run.py`
- [X] T021 [US1] Render first-run recommendation, acceptance, run progress, and pass result as stage cards in `src/verifysignal_spec/workflows/stage_cards.py`
- [X] T022 [US1] Update Codex generated guidance with first-run stage-card instructions in `src/verifysignal_spec/integrations/codex.py`
- [X] T023 [US1] Update Claude generated guidance with first-run stage-card instructions in `src/verifysignal_spec/integrations/claude.py`
- [X] T024 [US1] Update shared generated agent guidance constants for real-target-first recommendation and stage-card presentation in `src/verifysignal_spec/templates/agent_guidance.py`
- [X] T025 [US1] Update run and workflow command templates to instruct agents to use first-run stage cards in `src/verifysignal_spec/templates/agent-commands/verifysignal.run.md`
- [X] T026 [US1] Verify User Story 1 focused tests from `specs/009-golden-path-productization/quickstart.md`

**Checkpoint**: A user can complete the recommended first run on a real target
and receive an agent-chat-first strict pass presentation.

---

## Phase 4: User Story 2 - Experience Repair Value Loop (Priority: P1)

**Goal**: When the accepted first-run candidate fails for a repairable mechanical
reason, the product classifies the failure, auto-applies safe mechanical repairs
with clear before/after feedback, revalidates, reruns, and reports success only
after final strict pass.

**Independent Test**: In a temporary target workspace with a repairable first-run
failure fixture, repair output classifies root cause, auto-applies only safe
mechanical repair categories, preserves validation intent, emits repair stage
cards, requires confirmation for intent changes, and reaches `repaired-passed`
only after revalidation and rerun.

### Tests for User Story 2

- [X] T027 [P] [US2] Add failing contract tests for safe mechanical repair autonomy in `tests/contract/test_repair_autonomy_contract.py`
- [X] T028 [P] [US2] Add failing unit tests for auto-applicable versus confirmation-required repair categories in `tests/unit/test_repair_autonomy.py`
- [X] T029 [P] [US2] Add failing integration tests for repaired first-run strict pass in `tests/integration/test_golden_path_repair.py`
- [X] T030 [P] [US2] Add failing regression tests that data, credential, gate, and expected-behavior changes still require confirmation in `tests/contract/test_cli_repair_contract.py`

### Implementation for User Story 2

- [X] T031 [US2] Update safe repair classification and autonomy flags in `src/verifysignal_spec/workflows/repair_recommendations.py`
- [X] T032 [US2] Add repair feedback model conversion for before/after, autonomy, intent-preserved, revalidation, and rerun fields in `src/verifysignal_spec/workflows/models.py`
- [X] T033 [US2] Emit repair stage cards and repair feedback from `src/verifysignal_spec/commands/repair.py`
- [X] T034 [US2] Implement auto-application path for safe mechanical first-run repairs in `src/verifysignal_spec/commands/repair.py`
- [X] T035 [US2] Preserve confirmation-required behavior for data, credential, gate, target, and expected-behavior changes in `src/verifysignal_spec/workflows/repair_recommendations.py`
- [X] T036 [US2] Classify `repaired-passed` first-run status after revalidation and rerun in `src/verifysignal_spec/commands/run.py`
- [X] T037 [US2] Update repair agent command guidance for auto-applied mechanical repair feedback in `src/verifysignal_spec/templates/agent-commands/verifysignal.repair.md`
- [X] T038 [US2] Update generated Codex and Claude repair guidance to distinguish auto-applied safe repair from confirmation-required changes in `src/verifysignal_spec/integrations/codex.py`
- [X] T039 [US2] Mirror generated Claude repair guidance updates in `src/verifysignal_spec/integrations/claude.py`
- [X] T040 [US2] Verify User Story 2 focused tests from `specs/009-golden-path-productization/quickstart.md`

**Checkpoint**: First-run repair can produce a transparent `repaired-passed`
outcome without weakening validation intent.

---

## Phase 5: User Story 3 - Learn From Canonical Examples (Priority: P2)

**Goal**: Users can learn from canonical examples without treating fake/demo
targets as the user-facing golden path or fallback.

**Independent Test**: Documentation, generated guidance, and deterministic
fixtures show public unauthenticated, authenticated secret-safe, repairable
failure, and conditional data examples, each with expected outcome, failure
modes, evidence expectations, and repeatable pass/fail/not-evaluated
interpretation.

### Tests for User Story 3

- [X] T041 [P] [US3] Add failing documentation contract tests for four canonical examples in `tests/contract/test_golden_path_examples_contract.py`
- [X] T042 [P] [US3] Add failing integration tests for repeatable canonical example validation coverage in `tests/integration/test_golden_path_examples.py`
- [X] T043 [P] [US3] Add failing secret-safety tests for canonical example text in `tests/unit/test_workflow_secret_safety.py`

### Implementation for User Story 3

- [X] T044 [US3] Add deterministic canonical example fixture/workspace builders for public unauthenticated, authenticated secret-safe, repairable failure, and conditional/data-dependent examples in `tests/fixtures/workflows/golden_path_productization.py`
- [X] T045 [US3] Document the real-target-first golden path and canonical examples in `docs/golden-path.md`
- [X] T046 [US3] Add public unauthenticated and authenticated secret-safe example guidance in `docs/golden-path.md`
- [X] T047 [US3] Add repairable failure and conditional data example guidance with pass/fail/not-evaluated interpretation in `docs/golden-path.md`
- [X] T048 [US3] Link golden-path examples from `README.md`
- [X] T049 [US3] Update understand/specify agent command guidance so examples are optional learning aids after first-run recommendation in `src/verifysignal_spec/templates/agent-commands/verifysignal.understand.md`
- [X] T050 [US3] Mirror specify-stage example guidance in `src/verifysignal_spec/templates/agent-commands/verifysignal.specify.md`
- [X] T051 [US3] Verify User Story 3 documentation and repeatable example checks from `specs/009-golden-path-productization/quickstart.md`

**Checkpoint**: Canonical examples teach product behavior without becoming the
first-run fallback path.

---

## Phase 6: User Story 4 - Recover From Common Failures (Priority: P2)

**Goal**: Users can recover from missing Core, unreachable target, malformed
payload, missing runtime values, stale guidance, older workspace state, and
browser timing/selector failures without weakening validation intent.

**Independent Test**: Each induced failure category produces a stage card or CLI
summary with category, safe recovery action, and exact next command or decision.

### Tests for User Story 4

- [X] T052 [P] [US4] Add failing contract tests for blocked first-run prerequisite statuses in `tests/contract/test_golden_path_troubleshooting_contract.py`
- [X] T053 [P] [US4] Add failing integration tests for missing Core, unreachable target, and stale guidance recovery in `tests/integration/test_golden_path_troubleshooting.py`
- [X] T054 [P] [US4] Add failing contract tests for Golden Path Workspace State inspect/reset JSON in `tests/contract/test_golden_path_workspace_state_contract.py`
- [X] T055 [P] [US4] Add failing integration tests for older `.verifysignal/` state, resume hints, inspect, reset preview, confirmed reset, and preservation of unrelated artifacts in `tests/integration/test_golden_path_workspace_state.py`

### Implementation for User Story 4

- [X] T056 [US4] Add first-run blocker classification for missing target, unreachable target, unresolved credentials, stale inventory, stale workspace state, and incompatible Core in `src/verifysignal_spec/workflows/first_run.py`
- [X] T057 [US4] Add blocker stage cards for check, validate, run, repair, and workspace-state failures in `src/verifysignal_spec/workflows/stage_cards.py`
- [X] T058 [US4] Surface first-run blocker recovery commands from `src/verifysignal_spec/commands/validate.py`
- [X] T059 [US4] Surface first-run blocker recovery commands from `src/verifysignal_spec/commands/run.py`
- [X] T060 [US4] Add Golden Path Workspace State ownership classification and reset-preview helpers in `src/verifysignal_spec/workflows/repository.py`
- [X] T061 [US4] Implement `workflow inspect-golden-path-state` and `workflow reset-golden-path-state` command handlers and argparse subcommands in `src/verifysignal_spec/commands/workflow.py` and `src/verifysignal_spec/cli.py`
- [X] T062 [US4] Document common golden-path recovery paths, including older workspace state and safe inspect/reset, in `docs/golden-path-troubleshooting.md`
- [X] T063 [US4] Update check, validate, and run agent command templates with stage-card blocker guidance in `src/verifysignal_spec/templates/agent-commands/verifysignal.validate.md`
- [X] T064 [US4] Mirror blocker and workspace-state guidance in run and repair templates in `src/verifysignal_spec/templates/agent-commands/verifysignal.run.md`
- [X] T065 [US4] Verify User Story 4 troubleshooting and workspace-state checks from `specs/009-golden-path-productization/quickstart.md`

**Checkpoint**: Predictable first-run failures are recoverable and do not
recommend weakening required gates.

---

## Phase 7: User Story 5 - Prove Release Readiness (Priority: P3)

**Goal**: Maintainers have a repeatable checklist proving the golden path is
demoable, documented, secret-safe, Core-compatible, and regression-tested.

**Independent Test**: Running the readiness checklist produces a pass/fail
result for documentation, examples, workflow output, troubleshooting, secret
safety, Core compatibility, and regression coverage.

### Tests for User Story 5

- [X] T066 [P] [US5] Add failing contract tests for release-readiness checklist coverage, including explicit `ready to demo` and `ready to release` definitions, in `tests/contract/test_golden_path_readiness_contract.py`
- [X] T067 [P] [US5] Add failing integration tests for golden-path readiness quickstart coverage in `tests/integration/test_golden_path_readiness.py`

### Implementation for User Story 5

- [X] T068 [US5] Complete release-readiness checklist documentation with separate `ready to demo` and `ready to release` criteria in `docs/release-readiness.md`
- [X] T069 [US5] Link release-readiness guidance from `README.md`
- [X] T070 [US5] Add golden-path readiness commands to `specs/009-golden-path-productization/quickstart.md`
- [X] T071 [US5] Verify User Story 5 readiness checks from `specs/009-golden-path-productization/quickstart.md`

**Checkpoint**: Maintainers can validate release/demo readiness in 15 minutes or
less.

---

## Final Phase: Polish & Cross-Cutting Concerns

**Purpose**: Regression coverage, version impact, and consistency checks across
all delivered stories.

- [X] T072 [P] Update generated template documentation index in `src/verifysignal_spec/templates/README.md`
- [X] T073 [P] Review package version impact and update `pyproject.toml` and `src/verifysignal_spec/__init__.py` if the completed behavior requires a bump
- [X] T074 Run focused quickstart verification commands and record any deviations in `specs/009-golden-path-productization/quickstart.md`
- [X] T075 Run full regression suite with `.venv/bin/pytest -q` using `specs/009-golden-path-productization/quickstart.md`
- [X] T076 Run cross-artifact consistency review against `specs/009-golden-path-productization/spec.md`, `plan.md`, and `tasks.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 Setup**: No dependencies.
- **Phase 2 Foundational**: Depends on Phase 1.
- **US1 Complete First Golden Path**: Depends on Phase 2.
- **US2 Experience Repair Value Loop**: Depends on Phase 2 and integrates with
  US1 first-run state; can begin after US1 contracts are stable.
- **US3 Learn From Canonical Examples**: Depends on Phase 2; can proceed in
  parallel with US2 after US1 terms are stable.
- **US4 Recover From Common Failures**: Depends on Phase 2 and should run after
  US1 first-run state exists.
- **US5 Prove Release Readiness**: Depends on US1-US4.
- **Final Phase**: Depends on selected story scope being complete.

### User Story Dependencies

- **US1 (P1)**: Required MVP foundation for first-run recommendation, acceptance,
  strict pass, and stage-card UX.
- **US2 (P1)**: Required MVP repair recovery path; depends on US1 state and
  stage-card primitives.
- **US3 (P2)**: Documents and validates examples after the primary first-run
  journey exists.
- **US4 (P2)**: Adds recovery polish after first-run and repair semantics are
  available.
- **US5 (P3)**: Release readiness after productization scenarios exist.

### Within Each User Story

- Write tests first and confirm they fail for the expected reason.
- Implement the minimum code or documentation to satisfy that story.
- Run the story's focused tests before moving to lower-priority work.
- Keep Core interaction behind public CLI JSON contracts.
- Do not persist credential values in any artifact, output, or test fixture.

## Parallel Opportunities

- T001-T003 can run in parallel.
- T004, T005, and T006 can run in parallel before shared implementation.
- US1 test tasks T011-T015 can run in parallel.
- US2 test tasks T027-T030 can run in parallel.
- US3 documentation, example-coverage, and secret-safety tests T041-T043 can run in parallel.
- US4 failure-mode and workspace-state tests T052-T055 can run in parallel.
- US5 readiness tests T066-T067 can run in parallel.
- Documentation updates in US3 and US5 can proceed in parallel with code once
  US1 terminology stabilizes.

## Parallel Example: User Story 1

```text
Task: "T011 Contract tests in tests/contract/test_first_run_recommendation_contract.py"
Task: "T012 Ranking unit tests in tests/unit/test_first_run_recommendation.py"
Task: "T013 Stage-card contract tests in tests/contract/test_agent_chat_stage_card_contract.py"
Task: "T014 First-run integration tests in tests/integration/test_golden_path_first_run.py"
Task: "T015 Agent guidance integration tests in tests/integration/test_workflow_agent_public_guidance.py"
```

## Parallel Example: User Story 2

```text
Task: "T027 Repair autonomy contract tests in tests/contract/test_repair_autonomy_contract.py"
Task: "T028 Repair autonomy unit tests in tests/unit/test_repair_autonomy.py"
Task: "T029 Repaired first-run integration tests in tests/integration/test_golden_path_repair.py"
Task: "T030 Confirmation regression tests in tests/contract/test_cli_repair_contract.py"
```

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to deliver real-target-first recommendation, accept/skip, strict
   pass, and agent-chat stage cards.
3. Complete US2 to deliver first-run repair recovery and `repaired-passed`.
4. Stop and validate the MVP with the quickstart focused tests.

### Incremental Delivery

1. US1: First-run recommendation and strict pass.
2. US2: Repair recovery path and safe mechanical autonomy.
3. US3: Canonical examples as learning support with repeatable validation
   coverage.
4. US4: Troubleshooting and recovery polish.
5. US5: Release-readiness checklist.

### Validation Strategy

- Every behavior change starts with focused failing tests.
- Run adjacent regression tests for run, repair, workflow, integration
  installation, secret safety, and Core public contract behavior.
- Finish with `.venv/bin/pytest -q` and version-impact review.
