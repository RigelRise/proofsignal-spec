# Feature Specification: Golden Path Onboarding

**Feature Branch**: `010-golden-path-onboarding`  
**Created**: 2026-05-30  
**Status**: Draft  
**Input**: User description: "vamos especificar baseado na proposta de ajuste de produto"

## Constitution Alignment *(mandatory)*

- **Public Core boundary**: First-run onboarding must use only public ProofSignal
  Spec and ProofSignal Core command results. It must not depend on private Core
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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Product-owned first-run recommendation (Priority: P1)

A new user asks ProofSignal to start specifying validations in an existing
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

---

### User Story 2 - Smooth missing-understanding onboarding (Priority: P2)

A user runs the specify command before repository understanding exists. Instead
of stopping with a detached instruction, the product guides the user through
safe preparation and returns to the first-run recommendation without repeated
manual approvals.

**Why this priority**: The current experience breaks momentum at the exact point
where the product needs to feel guided. Missing understanding is normal for a
new workspace and should be handled as part of onboarding.

**Independent Test**: Start from a clean target repository with no ProofSignal
understanding artifacts and run the specify flow. The user should reach the
first-run recommendation with at most one explicit approval for safe inspection.

**Acceptance Scenarios**:

1. **Given** no repository understanding exists, **When** the user starts
   specifying validations, **Then** the product explains that understanding is
   needed and proceeds through safe preparation automatically when allowed.
2. **Given** the integration cannot auto-continue due to host permission rules,
   **When** preparation is needed, **Then** the user is asked once with a clear
   reason and the flow resumes after approval.
3. **Given** safe preparation succeeds, **When** the recommendation is displayed,
   **Then** the user is not required to manually restart the original specify
   command.

---

### User Story 3 - Clear integration install guidance (Priority: P3)

A user installs an agent integration and immediately sees what to run next, what
the product will do, what will not be inspected without approval, and what a
successful first-run experience should look like.

**Why this priority**: Installation is the first chance to set expectations. If
the integration installs files but gives no practical guide, the first command
has to explain too much and the experience feels accidental.

**Independent Test**: Install an integration in a sample repository and inspect
the terminal output plus generated guidance. A new user must be able to identify
the next command and the recommended first-run flow without external docs.

**Acceptance Scenarios**:

1. **Given** an integration install completes, **When** the user reads the
   output, **Then** it clearly explains the next command and the expected golden
   path.
2. **Given** generated agent guidance is installed, **When** a user opens it,
   **Then** it describes how first-run recommendation, acceptance, skip, repair,
   and success are reported.
3. **Given** a user is concerned about repository safety, **When** they read the
   install guidance, **Then** it clearly states that sensitive files and secret
   values are not inspected or persisted by default.

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
- The simplest behavior depends on external data that may be empty or unstable.
- The active branch contains a highly relevant but credential-heavy feature.
- Safe repository inspection cannot proceed automatically because the host
  requires user approval.
- Understanding exists but is stale relative to the current project state.
- A first-run execution fails, receives a safe automatic repair, and then passes.
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
- **FR-004**: The system MUST still surface branch-relevant or product-priority
  candidates separately from the first-run recommendation.
- **FR-005**: The system MUST present the recommended first run with an
  assertive explanation that accepting it is highly recommended for the first
  ProofSignal experience, while making it clear that the user can choose other
  use cases afterward.
- **FR-006**: The system MUST allow the user to accept or skip the golden path
  and MUST record that choice in project-local state.
- **FR-007**: When repository understanding is missing during specification, the
  system MUST guide the user through safe preparation and return to the original
  first-run selection flow.
- **FR-008**: Safe repository preparation SHOULD require no additional user
  action in integrations that allow automatic local inspection; where explicit
  approval is required, the system MUST ask once with a clear reason.
- **FR-009**: Integration installation MUST provide an immediate onboarding
  guide that explains the next command, the recommended first-run path, safety
  boundaries, and what success or repair means.
- **FR-010**: Repository understanding MUST capture source traceability for each
  candidate use case before it can be recommended.
- **FR-011**: Ordinary public project identifiers, including commit identifiers,
  branch names, route paths, and file paths, MUST NOT be rejected as secrets
  unless they contain additional secret-like context.
- **FR-012**: If understanding persistence fails, the system MUST provide
  actionable, user-readable guidance about the missing or invalid information
  without requiring the assistant to infer hidden field contracts.
- **FR-013**: First-run success MUST be tracked as successful when the selected
  use case passes directly or passes after safe automatic repair that preserves
  the approved validation intent.
- **FR-014**: First-run results MUST be presented in chat-first form with clear
  stage markers, status labels, summaries, and next actions.
- **FR-015**: The system MUST preserve existing manual use-case selection for
  users who skip the golden path.

### Key Entities *(include if feature involves data)*

- **First-Run Candidate**: A discovered validation opportunity with suitability
  signals such as authentication need, setup complexity, data stability,
  destructiveness, surface count, evidence clarity, and source traceability.
- **Branch-Relevant Candidate**: A discovered validation opportunity connected
  to the user's active work or recent repository changes. It can be high value
  without being appropriate as the first run.
- **Golden Path Choice**: The user's project-local decision to accept or skip
  the recommended first run, including the selected alias and current status.
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

## Assumptions

- The primary first-run user is new to ProofSignal and is evaluating whether the
  product can produce a trustworthy browser validation from their existing app.
- A useful first run should favor confidence and demonstration value over
  maximum business importance.
- Safe local repository inspection may read ordinary source, project metadata,
  and generated ProofSignal workspace files, but not local secret files without
  explicit user approval.
- Existing workflow stages, manual use-case selection, and repair semantics
  remain available; this feature improves the onboarding path rather than
  removing expert control.
