# Feature Specification: Golden Path Onboarding

**Feature Branch**: `010-golden-path-onboarding`  
**Created**: 2026-05-30  
**Status**: Draft  
**Input**: User description: "vamos especificar baseado na proposta de ajuste de produto"

## Constitution Alignment *(mandatory)*

- **Public Core boundary**: First-run onboarding must use only public VerifySignal
  Spec and VerifySignal Core command results. It must not depend on private Core
  packages, private report internals, or assistant-only heuristics.
- **Project-local workspace portability**: First-run recommendation, acceptance,
  skip, and outcome state must remain project-local and portable across supported
  integrations so a user can continue without the original assistant session.
- **Secret safety**: Repository understanding and recommendation must avoid
  sensitive files by default, must not persist credentials, and must not treat
  ordinary public project identifiers as secrets.
- **Agent-neutral interface**: The product must own the golden-path selection and
  onboarding prompts. Codex, Claude, and non-AI users must receive the same
  ranked first-run recommendation and status semantics.
- **Testable delivery**: The feature must be proven with repeatable scenarios for
  install guidance, missing-understanding onboarding, first-run ranking,
  branch-relevant recommendation separation, safe repository inspection, and
  first-run outcome tracking.

## Clarifications

### Session 2026-05-30

- Q: What should happen when no candidate meets ideal first-run criteria? → A: Recommend the lowest-risk existing candidate, clearly label any risk, and require explicit user acceptance before running it.
- Q: How should specify handle missing repository understanding? → A: Auto-prepare safe repository understanding during specify, pause only when host permissions or sensitive access require explicit approval, then resume first-run recommendation.
- Q: Where should integration install guidance appear? → A: Show terminal next steps and generate or update local integration guidance, with visually rich markers, colors, sections, statuses, and readable fallback when color is unavailable.
- Q: How should stale understanding affect the golden path? → A: Golden path applies only to the first run, respects existing understanding freshness rules, and relies on understand attempting to complete the full use-case inventory.
- Q: What happens after the user accepts the golden path? → A: Acceptance starts a guided end-to-end first-run flow through authoring, validation, execution, safe repair when needed, and final outcome.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Product-owned first-run recommendation (Priority: P1)

A new user asks VerifySignal to start specifying validations in an existing
repository. The product identifies the simplest reliable existing behavior as
the recommended first run, explains why accepting it is highly recommended, and
keeps more complex or branch-specific suggestions visible as secondary choices.

**Why this priority**: The first run is the user's first proof that the product
works. If the system recommends an authenticated, unstable, or branch-specific
flow as the first experience, the user loses trust before seeing value.

**Independent Test**: Run the onboarding recommendation on a repository that has
both trivial public flows and a complex active branch flow. The recommended
first run must be the simplest reliable public behavior, while the branch-specific
flow remains listed separately.

**Acceptance Scenarios**:

1. **Given** repository understanding includes a public unauthenticated page and
   an authenticated active-branch feature, **When** the user asks to specify a
   first validation, **Then** the public unauthenticated page is recommended as
   the first run.
2. **Given** the active branch points to a high-priority product change, **When**
   recommendations are shown, **Then** that change is labeled as branch-relevant
   but not allowed to replace the best first-run recommendation.
3. **Given** a first-run candidate is recommended, **When** the prompt is shown,
   **Then** the user sees a strong recommendation to accept it first, an
   explanation that other use cases can be chosen later, and a clear option to
   skip the golden path.
4. **Given** the user accepts the recommended first run, **When** the acceptance
   is recorded, **Then** the product guides the user through authoring,
   validation, execution, safe repair when needed, and final outcome reporting.

---

### User Story 2 - Smooth missing-understanding onboarding (Priority: P2)

A user runs the specify command before repository understanding exists. Instead
of stopping with a detached instruction, the product guides the user through
safe preparation automatically when possible and returns to the first-run
recommendation without repeated manual approvals.

**Why this priority**: The current experience breaks momentum at the exact point
where the product needs to feel guided. Missing understanding is normal for a
new workspace and should be handled as part of onboarding.

**Independent Test**: Start from a clean target repository with no VerifySignal
understanding artifacts and run the specify flow. The user should reach the
first-run recommendation with at most one explicit approval for safe inspection.

**Acceptance Scenarios**:

1. **Given** no repository understanding exists, **When** the user starts
   specifying validations, **Then** the product explains that understanding is
   needed, prepares safe repository understanding automatically when possible,
   and resumes first-run recommendation.
2. **Given** the integration cannot auto-continue due to host permission rules
   or sensitive access boundaries, **When** preparation is needed, **Then** the
   user is asked once with a clear reason and the flow resumes after approval.
3. **Given** safe preparation succeeds, **When** the recommendation is displayed,
   **Then** the user is not required to manually restart the original specify
   command.

---

### User Story 3 - Clear integration install guidance (Priority: P3)

A user installs an agent integration and immediately sees what to run next, what
the product will do, what will not be inspected without approval, and what a
successful first-run experience should look like. The guidance is visually
strong and scannable, with clear sections, markers, statuses, and summaries.

**Why this priority**: Installation is the first chance to set expectations. If
the integration installs files but gives no practical guide, the first command
has to explain too much and the experience feels accidental.

**Independent Test**: Install an integration in a sample repository and inspect
the terminal output plus generated guidance. A new user must be able to identify
the next command and the recommended first-run flow without external docs.

**Acceptance Scenarios**:

1. **Given** an integration install completes, **When** the user reads the
   terminal output, **Then** it clearly explains the next command and the
   expected golden path using visually distinct sections and status markers.
2. **Given** generated agent guidance is installed, **When** a user opens it,
   **Then** it describes how first-run recommendation, acceptance, skip, repair,
   and success are reported.
3. **Given** a user is concerned about repository safety, **When** they read the
   install guidance, **Then** it clearly states that sensitive files and secret
   values are not inspected or persisted by default.
4. **Given** color or rich terminal formatting is unavailable, **When** install
   guidance is displayed, **Then** the same next steps and statuses remain
   readable through plain-text structure.

---

### User Story 4 - Reliable understanding persistence (Priority: P4)

During onboarding, the repository understanding pass records enough traceability
to support recommendations without forcing the agent into trial-and-error
payload repairs.

**Why this priority**: The first experience should not expose internal schema
friction. False secret detection and missing trace fields make the product feel
fragile even when the repository scan was otherwise useful.

**Independent Test**: Run understanding on a representative repository with git
metadata and multiple candidate surfaces. The understanding output must persist
successfully on the first valid attempt and every candidate must be traceable to
inspected sources.

**Acceptance Scenarios**:

1. **Given** repository metadata contains a normal commit identifier, **When**
   understanding is persisted, **Then** it is not rejected as secret-looking
   data.
2. **Given** candidate use cases are generated, **When** they are persisted,
   **Then** each candidate includes source traceability back to inspected project
   surfaces.
3. **Given** a candidate is incomplete, **When** persistence validation runs,
   **Then** the user receives actionable product-language guidance instead of
   requiring the assistant to reverse-engineer field names.

### Edge Cases

- The repository has no obvious public, read-only, unauthenticated behavior.
  In this case, the system recommends the lowest-risk existing candidate only
  with clear risk labeling and explicit user acceptance before execution.
- The simplest behavior depends on external data that may be empty or unstable.
- The active branch contains a highly relevant but credential-heavy feature.
- Safe repository inspection cannot proceed automatically because the host
  requires user approval.
- Understanding exists but is stale relative to the current project state. For
  the first run, the golden path follows the existing understanding freshness
  rules before recommending; after the first run, understanding behavior remains
  the existing workflow.
- A first-run execution fails, receives a safe automatic repair, and then passes.
- The user accepts the golden path but required runtime data, host permission,
  or a safety boundary blocks automatic continuation.
- The user declines the recommended first run and chooses another use case.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST compute a first-run suitability ranking that is
  separate from product priority, branch relevance, and recency of code changes.
- **FR-002**: The system MUST prefer candidates with low first-run risk:
  unauthenticated access, read-only behavior, a single visible surface, stable
  rendered evidence, no credentials, no destructive actions, and no rare seed
  data requirements.
- **FR-003**: The system MUST demote candidates from first-run recommendation
  when they require authentication, privileged accounts, complex setup, write
  operations, tokenized links, billing, uploads, or multiple external services.
- **FR-004**: If no candidate satisfies all ideal first-run criteria, the system
  MUST recommend the lowest-risk existing candidate only when it clearly labels
  the unmet criteria and requires explicit user acceptance before execution.
- **FR-005**: The system MUST still surface branch-relevant or product-priority
  candidates separately from the first-run recommendation.
- **FR-006**: The system MUST present the recommended first run with an
  assertive explanation that accepting it is highly recommended for the first
  VerifySignal experience, while making it clear that the user can choose other
  use cases afterward.
- **FR-007**: The system MUST allow the user to accept or skip the golden path
  and MUST record that choice in project-local state.
- **FR-008**: Accepting the golden path MUST start a guided end-to-end first-run
  flow through authoring, validation, execution, safe repair when needed, and
  final outcome reporting.
- **FR-009**: The guided first-run flow MUST pause only for required runtime
  data, host permissions, or safety boundaries that cannot be resolved
  automatically, and MUST resume from the same stage after the blocker is
  resolved.
- **FR-010**: When repository understanding is missing during specification, the
  system MUST prepare safe repository understanding automatically when possible
  and then return to the original first-run selection flow.
- **FR-011**: Safe repository preparation MUST pause only when host permissions
  or sensitive access boundaries require explicit approval; when approval is
  required, the system MUST ask once with a clear reason and resume after
  approval.
- **FR-012**: Integration installation MUST provide immediate terminal next
  steps and generate or update local integration guidance that explain the next
  command, the recommended first-run path, safety boundaries, and what success
  or repair means.
- **FR-013**: Integration onboarding guidance MUST be visually scannable with
  clear sections, status markers, progress markers, concise summaries, and
  color or emphasis when available, while remaining readable as plain text.
- **FR-014**: Repository understanding MUST capture source traceability for each
  candidate use case before it can be recommended.
- **FR-015**: Ordinary public project identifiers, including commit identifiers,
  branch names, route paths, and file paths, MUST NOT be rejected as secrets
  unless they contain additional secret-like context.
- **FR-016**: For first-run recommendation, the system MUST respect the existing
  understanding freshness rules instead of defining a separate golden-path stale
  policy.
- **FR-017**: Repository understanding SHOULD attempt to complete the full
  discoverable use-case inventory whenever possible and MUST clearly label
  partial inventory before it is used for first-run recommendation.
- **FR-018**: If understanding persistence fails, the system MUST provide
  actionable, user-readable guidance about the missing or invalid information
  without requiring the assistant to infer hidden field contracts.
- **FR-019**: First-run success MUST be tracked as successful when the selected
  use case passes directly or passes after safe automatic repair that preserves
  the approved validation intent.
- **FR-020**: First-run results MUST be presented in chat-first form with clear
  stage markers, status labels, summaries, and next actions.
- **FR-021**: The system MUST preserve existing manual use-case selection for
  users who skip the golden path.

### Key Entities *(include if feature involves data)*

- **First-Run Candidate**: A discovered validation opportunity with suitability
  signals such as authentication need, setup complexity, data stability,
  destructiveness, surface count, evidence clarity, and source traceability.
- **Branch-Relevant Candidate**: A discovered validation opportunity connected
  to the user's active work or recent repository changes. It can be high value
  without being appropriate as the first run.
- **Golden Path Choice**: The user's project-local decision to accept or skip
  the recommended first run, including the selected alias, current guided-flow
  stage, and current status.
- **Onboarding Guidance**: The install-time and command-time instructions that
  explain how to start, what will be inspected, why the first run is recommended,
  and how outcomes are reported.
- **First-Run Outcome**: The recorded result of the accepted golden path,
  including direct pass, repaired pass, skipped, failed, or abandoned.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a representative repository with both trivial public flows and
  a complex active-branch flow, the recommended first run is the simplest
  reliable public behavior in 100% of evaluation runs.
- **SC-002**: From a clean repository with no understanding artifacts, a user can
  reach a first-run recommendation in under 3 minutes with no more than one
  explicit approval for safe local inspection.
- **SC-003**: Integration install output and generated guidance identify the
  next command and first-run expectation clearly enough that 90% of first-time
  evaluators can state the next action without reading external docs.
- **SC-004**: 100% of recommended candidates include traceability to inspected
  project surfaces before they can be persisted or displayed.
- **SC-005**: Normal commit identifiers and branch names are accepted as
  non-secret project metadata in 100% of safe-understanding persistence tests.
- **SC-006**: 95% of first-run recommendation summaries include both the
  recommended golden path and at least one separate explanation of why a
  branch-relevant candidate was not selected first when such a candidate exists.
- **SC-007**: First-run outcome tracking correctly classifies direct pass,
  repaired pass, skipped, failed, and abandoned outcomes in 100% of contract
  examples.
- **SC-008**: In moderated dogfood sessions, at least 80% of users rate the
  first-run onboarding as clear and confidence-building.
- **SC-009**: In examples with no ideal first-run candidate, 100% of
  recommendations label the unmet ideal criteria and require explicit acceptance
  before execution.
- **SC-010**: In clean-repository onboarding examples where safe inspection is
  allowed, 100% of specify flows return to first-run recommendation without the
  user manually restarting the command.
- **SC-011**: In terminal and generated-guidance examples, 90% of first-time
  evaluators can identify current stage, status, recommended next action, and
  safety boundary within 30 seconds.
- **SC-012**: In stale-understanding examples, 100% of first-run recommendations
  either use refreshed understanding according to the existing freshness rules
  or clearly label that the inventory remains partial before recommendation.
- **SC-013**: In accepted-golden-path examples, 100% of flows either reach a
  final first-run outcome or stop at a clearly labeled blocker with the blocked
  stage, required user action, and resume path.

## Assumptions

- The primary first-run user is new to VerifySignal and is evaluating whether the
  product can produce a trustworthy browser validation from their existing app.
- A useful first run should favor confidence and demonstration value over
  maximum business importance.
- Safe local repository inspection may read ordinary source, project metadata,
  and generated VerifySignal workspace files, but not local secret files without
  explicit user approval.
- Existing workflow stages, manual use-case selection, and repair semantics
  remain available; this feature improves the onboarding path rather than
  removing expert control.
