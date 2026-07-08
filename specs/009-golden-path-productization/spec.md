# Feature Specification: Golden Path Productization

**Feature Branch**: `009-golden-path-productization`  
**Created**: 2026-05-29  
**Status**: Draft  
**Input**: User description: "Objetivo: transformar o que ja foi construido em uma experiencia demonstravel, documentada e confiavel para um usuario novo. Golden Path Productization"

**Scope Decision**: The MVP golden path combines adoption plus differentiated repair value on a real target selected or confirmed by the user: a new user should initialize or use a clean target project, accept a product-recommended first validation candidate that is simple, existing, and expected to be stable, complete a first browser validation journey against a reachable application they care about, and get a clear repair experience only if that journey fails. The first run counts as successful when it reaches a strict validated pass either directly or after a repair cycle that classifies the failure, explains the repair, applies the fix, revalidates, reruns, and then passes. Because this is the user's first VerifySignal experience, the first-run UX must be presentation-quality: visually clear, confidence-building, easy to explain, and explicit about status, evidence, repair, and next action. If the user declines the recommended first run, the golden path is recorded as skipped rather than successful or failed. Fake or bundled demo targets are not part of the user-facing golden path or fallback story; deterministic fixtures may only be used internally for automated regression tests. Release/demo readiness remains supporting scope, not the primary MVP.

## Clarifications

### Session 2026-05-30

- Q: What concrete target should anchor the MVP golden path? → A: The MVP golden path must be real-target-first: it guides the user to validate a reachable real application target they care about. Fake/demo targets are not part of the user-facing golden path or fallback story; deterministic fixtures may only be used internally for automated regression tests.
- Q: What metric defines whether the golden path first run succeeded? → A: The first run succeeds when the simplest existing stable validation candidate that the product identifies and the user explicitly accepts reaches a strict validated pass, either directly or after a transparent repair cycle. If the user declines the recommended run, the golden path is recorded as skipped.
- Q: When should the MVP demonstrate repair value? → A: Repair is not a separate post-success demo. It is part of the first-run experience only when a failure occurs, and success still requires repair feedback, revalidation, rerun, and a final strict validated pass.
- Q: What autonomy policy should repair use in the golden path? → A: The product may auto-apply safe mechanical repairs such as selector, wait, ordering, target-specificity, and equivalent flow fixes with clear before/after feedback. Changes to validation intent, required gates, data assumptions, credentials, or expected product behavior require user confirmation.
- Q: How should the product identify and present the first-run candidate? → A: The product must inventory and rank candidates by low setup risk, reachable real target, no unresolved credentials, simple rendered evidence, and low data dependency. It must strongly recommend the top candidate as the best first test to see the product work, explain the rationale, ask the user to accept or skip, and clarify that other validations can be chosen after the first golden-path run.
- Q: What should be the primary first-run UX surface? → A: The primary experience is agent-chat first. Each stage and stage result must be displayed in the conversation with strong visual structure: clear sections, separators, status markers, concise summaries, evidence highlights, repair feedback, and next actions. Reports and artifacts support the chat experience but are not the primary surface.
- Q: What presentation contract should each first-run chat stage follow? → A: Each first-run stage must render a standardized stage card with title, status marker, one-line summary, why it matters, primary evidence, repair/change details when present, and next action.

## Constitution Alignment *(mandatory)*

- **Public Core boundary**: The golden path must demonstrate VerifySignal Spec through public CLI/workflow contracts and documented Core compatibility behavior only. It must not require reading private Core packages, installed package source files, or undocumented report internals to understand or complete the journey.
- **Real-target-first experience**: The first user-facing journey must require an explicit, reachable target chosen or confirmed by the user. Local fixtures may support automated regression coverage, but they must not be presented as the user's fallback path or primary product value.
- **Project-local workspace portability**: All golden-path state, generated use cases, run requests, skills, reports, and repair records must remain reviewable and portable under the target project's `.verifysignal/` workspace.
- **Secret safety**: The experience must use non-secret real targets, dummy values, or credential references. It must never ask a new user to paste real secrets into specs, run requests, skills, logs, or public summaries.
- **Agent-chat-first interface**: Codex and Claude conversations are the primary first-run surface. Deterministic non-AI CLI users must still receive equivalent semantics, but the most polished guided experience is delivered in chat.
- **First-run UX quality**: The first-run experience must be clear enough for a new user and polished enough for a product demo, with strong chat-native visual hierarchy for recommendation, progress, evidence, repair feedback, final status, and next action.
- **Testable delivery**: Each scenario must be repeatable with a clear pass/fail checklist covering setup, authoring, validation readiness, run execution, repair, troubleshooting, and release readiness.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete First Golden Path (Priority: P1)

A new user evaluating VerifySignal Spec wants one reliable path from installation or initialization to a meaningful browser validation result, without needing maintainer guidance or implementation knowledge.

**Why this priority**: The product becomes trustworthy when a first-time user can see the full value loop quickly: set up, choose a scenario, author artifacts, validate readiness, execute a run, and understand the result.

**Independent Test**: Can be tested by giving a clean environment and the golden-path instructions to a first-time evaluator, then verifying they complete the journey and can explain the final status without additional help.

**Acceptance Scenarios**:

1. **Given** a clean target project, a reachable real application target, and documented prerequisites, **When** a new user follows the golden path, **Then** the product inventories candidate validations, ranks them by first-run suitability, and strongly recommends the top candidate as the best first test to see the product work.
2. **Given** the top first-run candidate is presented, **When** the user reads the recommendation, **Then** the output explains the ranking rationale, states that accepting is highly recommended for the first golden-path run, asks the user to accept or skip, and clarifies that other validations can be chosen after the first run.
3. **Given** the user accepts the recommended first-run candidate, **When** the run completes without repair, **Then** the first run counts as successful only if Core/browser execution passes, Spec coverage is complete, all required gates have mapped rendered-result evidence, project-local artifacts are written, and the next action is clear.
4. **Given** the accepted first-run candidate fails for a repairable artifact or flow reason, **When** the product identifies a safe mechanical repair, **Then** it may apply the repair automatically, show clear before/after feedback, revalidate the repaired artifact, rerun, and count the golden path as successful only after the final run reaches the same strict validated pass criteria.
5. **Given** the proposed repair would change validation intent, required gates, data assumptions, credentials, or expected product behavior, **When** the repair flow reaches that decision, **Then** the product must request and record user confirmation before changing artifacts.
6. **Given** the user declines the recommended first-run candidate, **When** the workflow records the outcome, **Then** the golden path is marked as skipped rather than successful or failed.
7. **Given** the user reaches each workflow stage, **When** the stage completes or blocks, **Then** the output explains what happened, what it means, and the next recommended action.
8. **Given** the user has no prior VerifySignal context, **When** they inspect the generated artifacts, **Then** they can identify the use case, target environment, run request, skill, validation gates, and evidence expectations.
9. **Given** this is the user's first run, **When** the recommendation, run progress, repair feedback, or final result is displayed, **Then** the agent chat presents each stage as a standardized stage card with title, status marker, one-line summary, why it matters, primary evidence, repair/change details when present, and next action.

---

### User Story 2 - Experience Repair Value Loop (Priority: P1)

A new user whose accepted first-run candidate fails wants VerifySignal Spec to do more than generate artifacts: it should explain the failed browser run, preserve validation intent, present clear repair feedback, repair the artifact when appropriate, revalidate, rerun, and only count success after the repaired run passes.

**Why this priority**: The repair loop is the product's clearest differentiated value. It proves that the workflow can handle realistic browser instability without weakening required validation gates.

**Independent Test**: Can be tested by inducing or encountering a repairable failure in the accepted first-run path and verifying the output classifies the root cause, treats missing aborted-run coverage as diagnostic, shows clear repair feedback, revalidates the repaired artifacts, reruns, and reports success only after a strict validated pass.

**Acceptance Scenarios**:

1. **Given** the accepted first-run candidate fails after earlier UI evidence was available, **When** the repair flow runs, **Then** the result classifies the likely root cause instead of recommending broad gate weakening.
2. **Given** the product repairs selector, wait, ordering, target-specificity, or equivalent flow behavior, **When** the repair is shown to the user, **Then** the feedback explains what changed, why it was safe to auto-apply, and how validation intent was preserved.
3. **Given** the proposed repair affects validation intent, required gates, data assumptions, credentials, or expected product behavior, **When** the repair is shown to the user, **Then** the product requests and records user confirmation before changing artifacts.
4. **Given** the repair is applied, **When** readiness validation runs again, **Then** the output distinguishes authored evidence mapping from a full browser rerun and gives the next action.
5. **Given** the repaired use case reruns, **When** the run completes, **Then** the summary separates Core/browser status from Spec coverage status and counts the golden path as successful only after the final strict validated pass.

---

### User Story 3 - Learn From Canonical Examples (Priority: P2)

A prospective user wants representative examples that show how VerifySignal Spec behaves across the common cases they will encounter: simple public pages, authenticated flows, repairable browser failures, and conditional product data.

**Why this priority**: Examples turn the product from a flexible toolkit into a learnable workflow. The public-page and repairable-failure examples explain behavior around the MVP; authenticated and conditional examples broaden confidence after the first value loop is proven.

**Independent Test**: Can be tested by selecting each canonical example, following its documented path, and verifying the expected pass, fail, repair, or conditional result without changing product code.

**Acceptance Scenarios**:

1. **Given** a user wants the simplest possible demonstration, **When** they choose the public-page example, **Then** they can run it without credentials and see a complete result.
2. **Given** a user needs to understand credential-safe flows, **When** they choose the authenticated example, **Then** the guidance uses credential references or dummy data and never persists real secrets.
3. **Given** a user wants to understand repair, **When** they choose the repairable-failure example, **Then** the failed run is classified, the repair requires appropriate confirmation, and the rerun path is explicit.
4. **Given** an example includes optional or data-dependent UI, **When** the condition is absent, **Then** the result explains whether the gate was not evaluated, blocked, or failed.

---

### User Story 4 - Recover From Common Failures (Priority: P2)

A new user who hits a predictable setup, target, or workflow problem needs a concise troubleshooting path that helps them recover without weakening validation intent.

**Why this priority**: First-run failures are expected in browser validation products. The difference between a promising tool and a trusted product is whether those failures are understandable and recoverable.

**Independent Test**: Can be tested by inducing common failure modes and verifying the user-facing guidance identifies the category, safe recovery action, and next command or decision.

**Acceptance Scenarios**:

1. **Given** VerifySignal Core is missing or incompatible, **When** the user runs the golden path, **Then** the product stops before execution and shows setup or compatibility recovery guidance.
2. **Given** the target application is unavailable or redirects unexpectedly, **When** the run readiness or run stage detects it, **Then** the output distinguishes environment recovery from artifact repair.
3. **Given** a workflow payload is malformed or missing required fields, **When** the user persists or validates it, **Then** the error points to the public contract field and a corrective action.

---

### User Story 5 - Prove Release Readiness (Priority: P3)

A maintainer preparing a release wants a short, repeatable readiness checklist showing that the product can still demonstrate the golden path, explain failures, protect secrets, and preserve compatibility.

**Why this priority**: A polished release needs evidence that the product is not only technically correct but also teachable, demoable, and safe for new users.

**Independent Test**: Can be tested by running the release-readiness checklist and confirming each productization scenario has a clear pass/fail result and an owner-visible summary.

**Acceptance Scenarios**:

1. **Given** a maintainer is preparing a release, **When** they run the readiness checklist, **Then** it verifies documentation, examples, troubleshooting, compatibility, secret safety, and regression coverage.
2. **Given** a readiness item fails, **When** the maintainer reads the result, **Then** it identifies whether the release needs documentation, artifact, test, compatibility, or product behavior work.

### Edge Cases

- A user starts from a repository that already contains `.verifysignal/` artifacts from an older version.
- The selected real target is temporarily unavailable or returns empty data.
- The user has an agent integration installed but wants to complete the same flow without an agent.
- A repairable example produces a different failure category than expected.
- A credential-looking value appears in a target URL, runtime input, run log, screenshot summary, or repair confirmation.
- The user stops midway through the golden path and resumes from generated workspace state.
- The installed guidance is stale compared with the current package version.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The product MUST provide one primary golden-path journey for a new user that starts from a clean target project plus an explicit reachable real application target and ends with a strict validated pass for that target when the user accepts the recommended first-run candidate, either directly or after a transparent repair cycle.
- **FR-002**: The golden path MUST state prerequisites, target-selection requirements, expected duration, expected artifacts, expected results, and the safe cleanup or reset path.
- **FR-003**: The golden path MUST explain the purpose of each workflow stage in user-facing language before asking the user to perform or approve the stage.
- **FR-004**: The MVP golden path MUST include repair only as failure recovery for the accepted first-run journey: when the run fails for a repairable reason, the product MUST classify the failure, show clear repair feedback, repair without weakening validation intent, revalidate, rerun, and require a final strict validated pass before reporting success.
- **FR-005**: The product MUST provide canonical examples for at least a public unauthenticated page, an authenticated flow with secret-safe credential handling, a repairable browser failure, and a conditional or data-dependent result.
- **FR-006**: Each canonical example MUST include expected outcomes, known failure modes, evidence expectations, and a clear pass/fail or not-evaluated interpretation without positioning fake/demo targets as the user-facing fallback path.
- **FR-007**: The product MUST make validation readiness visibly distinct from full browser run execution throughout the golden-path documentation and examples.
- **FR-008**: The product MUST show Core/browser execution status separately from Spec coverage status in golden-path run and repair examples.
- **FR-009**: The product MUST provide troubleshooting guidance for missing or incompatible Core, unreachable targets, malformed workflow payloads, missing runtime values, stale generated guidance, and repairable browser timing or selector failures.
- **FR-010**: Troubleshooting guidance MUST preserve validation intent and MUST NOT recommend weakening required gates unless the user explicitly changes the expected product behavior through clarification, planning, or an equivalent recorded confirmation.
- **FR-011**: The product MUST keep all golden-path examples and instructions secret-safe by using non-secret targets, dummy values, or references rather than persisted credentials.
- **FR-012**: Codex and Claude agent chats MUST be the primary first-run UX surfaces, while non-AI CLI users MUST still be able to complete an equivalent journey and understand equivalent result semantics.
- **FR-013**: The product MUST include a release-readiness checklist that verifies documentation, examples, workflow outputs, troubleshooting, secret safety, compatibility, and regression coverage.
- **FR-014**: The product MUST define what counts as "ready to demo" and "ready to release" for the golden path.
- **FR-015**: The product MUST provide a way for users to inspect or reset Golden Path Workspace State without losing unrelated user-authored artifacts or unrelated `.verifysignal/` use cases, run requests, skills, reports, and repair records.
- **FR-016**: The product MUST include repeatable validation coverage for the golden path and its representative failure/recovery scenarios.
- **FR-017**: Before the first run, the product MUST inventory candidate validations in the user's project, rank them by low setup risk, reachable real target, no unresolved credentials, simple rendered evidence, and low data dependency, then recommend the top candidate.
- **FR-018**: The first-run success metric MUST require a strict validated pass, either directly or after repair: Core/browser execution passed, Spec coverage complete, all required gates mapped to rendered-result evidence, run artifacts written under `.verifysignal/`, repair feedback recorded when repair occurred, and a clear next action shown.
- **FR-019**: If the user declines the recommended first-run candidate, the product MUST record the golden path as skipped and MUST NOT count it as successful, failed, or inconclusive.
- **FR-020**: The repair flow MAY auto-apply safe mechanical repairs, including selector, wait, ordering, target-specificity, and equivalent flow fixes, when the repair preserves validation intent and includes clear before/after feedback.
- **FR-021**: The repair flow MUST require and record user confirmation before applying changes that affect validation intent, required gates, data assumptions, credentials, or expected product behavior.
- **FR-022**: The first-run recommendation MUST explicitly state that accepting the top candidate is highly recommended as the best first test to see VerifySignal Spec work, while making clear that the user can choose other validations after completing or skipping the first golden-path run.
- **FR-023**: The first-run agent-chat UX MUST present recommendation, progress, evidence, repair feedback, final status, and next action as standardized stage cards with title, status marker, one-line summary, why it matters, primary evidence, repair/change details when present, and next action.
- **FR-024**: The first-run UX MUST avoid dumping raw logs as the primary experience; raw details may remain available, but the agent-chat primary view must summarize status, confidence, evidence, and actionability first.
- **FR-025**: Reports, Markdown, HTML, JSON, and workspace artifacts MAY support inspection and sharing, but they MUST NOT replace the agent chat as the primary first-run experience.

### Key Entities *(include if feature involves data)*

- **Golden Path Journey**: The primary first-user experience, including prerequisites, commands or actions, expected outputs, generated artifacts, and completion criteria.
- **Agent-Chat Stage Card**: A standardized chat presentation block for a first-run stage, including title, status marker, one-line summary, why it matters, primary evidence, repair/change details when present, and next action.
- **Agent-Chat First-Run UX**: The primary conversational presentation of the first run, composed of stage cards plus concise connective guidance.
- **First-Run Candidate**: A product-ranked validation candidate selected from the user's real project for low setup risk, stable rendered evidence, no unresolved credentials, and low data dependency.
- **Canonical Example**: A representative use case that teaches one important product behavior, such as public validation, authenticated validation, repair, or conditional evidence.
- **Repair Value Loop**: The first-run failure-recovery journey that demonstrates root-cause classification, clear repair feedback, artifact repair, revalidation, rerun, and final strict validated pass.
- **Troubleshooting Outcome**: A documented recovery path for a predictable failure category, including user-facing diagnosis, safe action, and next step.
- **Release Readiness Checklist**: A maintainer-facing checklist that proves the product is demoable, documented, safe, and regression-tested.
- **Golden Path Workspace State**: Project-local generated artifacts and run history created while following the golden path.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A first-time evaluator can complete the adoption golden path from clean target project to strict validated pass for an accepted first-run candidate in 10 minutes or less using only documented guidance.
- **SC-002**: At least 90% of first-time evaluators in a guided usability check can identify the basic current status and next action after each golden-path stage without maintainer help.
- **SC-003**: When the accepted first-run candidate has a repairable failure, a first-time evaluator can complete the repair value loop from failure classification to final strict validated pass in 10 minutes or less.
- **SC-004**: At least four canonical examples are documented and have repeatable pass/fail validation coverage through deterministic fixtures or temporary workspaces for public unauthenticated, authenticated secret-safe, repairable failure, and conditional or data-dependent examples.
- **SC-005**: 100% of golden-path instructions and examples avoid private implementation inspection and avoid persisting real credential values.
- **SC-006**: A repairable first-run failure produces a classified root cause, preserves required-gate intent, auto-applies only safe mechanical repairs, records clear before/after repair feedback plus any required confirmation, and reaches a final strict validated pass in one guided cycle.
- **SC-007**: A maintainer can complete the release-readiness checklist in 15 minutes or less and see a clear pass/fail result for every item.
- **SC-008**: Users can recover from the documented missing Core, unreachable target, and malformed workflow input scenarios in 5 minutes or less per scenario using troubleshooting guidance.
- **SC-009**: Existing workflow regression tests continue to pass while the golden-path scenarios are covered.
- **SC-010**: At least 90% of first-time evaluators understand that the recommended first-run candidate is the best initial test to see the product work and that other validations remain available after the first run.
- **SC-011**: At least 90% of first-time evaluators can explain each first-run stage status, why it mattered, primary evidence, repair outcome if any, and next action from the agent-chat stage cards without reading raw logs, opening secondary reports, or asking a maintainer.

## Assumptions

- The MVP golden path relies on a reachable real application target selected or confirmed by the user; local or bundled fixtures are limited to internal automated regression coverage.
- Existing workflow guardrails, public Core boundary, secret-safety behavior, and repair semantics remain in force.
- Documentation, examples, generated guidance, and release-readiness artifacts are part of the product experience, not separate marketing material.
- The first-user audience includes maintainers evaluating the product locally and agent users invoking generated VerifySignal workflow commands.
- Release readiness focuses on local package quality and demoability; publishing automation can be planned separately if needed.
