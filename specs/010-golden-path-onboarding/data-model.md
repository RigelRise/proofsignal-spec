# Data Model: Golden Path Onboarding

## FirstRunSuitabilityScore

Ranks a discovered validation candidate for the first run.

**Fields**

- `candidateAlias`: Candidate alias being scored.
- `rank`: 1-based rank after sorting.
- `score`: Integer score from 0 to 100.
- `idealCriteriaMet`: List of ideal first-run criteria satisfied.
- `idealCriteriaMissing`: List of unmet ideal criteria that must be explained
  before acceptance.
- `requiresExplicitAcceptance`: Boolean, true when the candidate is recommended
  despite missing ideal criteria.
- `branchRelevant`: Boolean, true when the candidate is tied to active branch or
  recent work.
- `branchRelevanceReason`: Optional explanation shown separately from
  first-run suitability.
- `suitabilityRationale`: User-facing explanation of why the candidate is or is
  not a safe first run.
- `blockers`: Blocking reasons that prevent recommendation.

**Validation rules**

- A candidate with unresolved credential values cannot be ideal for first run.
- A candidate may be recommended with missing ideal criteria only when it is the
  lowest-risk existing candidate and `requiresExplicitAcceptance` is true.
- Branch relevance cannot increase rank above a lower-risk simple candidate.
- Each scored candidate must reference source inventory items.

## FirstRunIdealCriteria

The reusable checklist for a high-confidence first run.

**Fields**

- `publicOrUnauthenticated`: No login or privileged account required.
- `readOnly`: Does not mutate product data or trigger external side effects.
- `singleVisibleSurface`: Validates one route/page/tool surface.
- `stableRenderedEvidence`: Has visible rendered evidence that can be checked
  without fragile timing or hidden data.
- `noCredentials`: Requires no credential values or runtime secret references.
- `lowExternalDependency`: Does not depend on rare seed data, token links,
  billing, uploads, or multiple external services.
- `safeToAutoGuide`: Can be guided through authoring/validation/run without
  extra product decisions.

**Validation rules**

- Missing criteria must be listed in recommendation output.
- Missing criteria require explicit acceptance before execution.

## GuidedFirstRunState

Tracks the accepted Golden Path from recommendation through final outcome.

**Fields**

- `schemaVersion`: `verifysignal-spec-guided-first-run/v1`.
- `selectedCandidate`: Accepted alias.
- `stage`: `recommended`, `accepted`, `authoring`, `validating`, `running`,
  `repairing`, `passed`, `repaired-passed`, `failed`, `blocked`, or `skipped`.
- `stageStartedAt`: Timestamp for the current stage.
- `firstRunStatus`: Public outcome status.
- `strictPass`: Boolean when final outcome is a strict pass.
- `blocker`: Optional blocker with category, required action, and resume path.
- `resumeCommand`: Next command or agent action to continue from the current
  stage.
- `stageCards`: Current chat-first stage cards.
- `ownedArtifacts`: Golden-path-owned artifacts created by the guided flow.

**State transitions**

- `recommended` -> `accepted` when the user accepts the recommendation.
- `accepted` -> `authoring` when artifact generation starts.
- `authoring` -> `validating` after run request and skill artifacts are ready.
- `validating` -> `running` after authoring/runtime readiness passes.
- `running` -> `repairing` when a safe repairable failure is detected.
- `repairing` -> `repaired-passed` after repair, revalidation, rerun, and
  strict pass.
- `running` -> `passed` after direct strict pass.
- Any active stage -> `blocked` when required runtime data, permissions, safety
  boundaries, or Core incompatibility stop progress.
- `recommended` -> `skipped` when the user declines.

## OnboardingGuidance

Represents install-time and command-time guidance for a new user.

**Fields**

- `integrationKey`: Integration key such as `codex` or `claude`.
- `terminalSummary`: Concise terminal next steps.
- `generatedGuidePath`: Local guide path when generated.
- `stageMarkers`: Ordered marker labels used in terminal/chat.
- `usesColor`: Whether color/emphasis is used when available.
- `plainTextFallback`: Equivalent plain text guidance.
- `nextCommand`: Recommended command after install.
- `safetyBoundaries`: Safe inspection and sensitive-file boundaries.
- `successSemantics`: Direct pass, repaired pass, skip, fail, and blocked
  meaning.

**Validation rules**

- Terminal and generated guidance must both include next command, safety
  boundaries, and first-run success semantics.
- Guidance must remain readable without color.
- Guidance must not include credential values.

## UnderstandingOnboardingResult

Summarizes safe understanding preparation during onboarding.

**Fields**

- `status`: `complete`, `partial`, `stale`, `blocked`, or `failed`.
- `scope`: Scope used for the inventory pass.
- `generatedGitHash`: Public git revision metadata when available.
- `sourceFilesVisited`: Count of source files inspected.
- `candidateCount`: Number of candidate use cases produced.
- `trivialCandidateCount`: Number of candidates satisfying ideal first-run
  criteria.
- `sourceTraceabilityStatus`: `complete`, `normalized`, or `missing`.
- `partialInventoryReasons`: Reasons inventory remains partial.
- `nextAction`: Next step when blocked or partial.

**Validation rules**

- Normal commit hashes, branch names, route paths, and file paths are public
  metadata unless they contain secret-bearing context.
- Candidate use cases cannot be recommended without source traceability.
- Partial inventory must be clearly labeled before first-run recommendation.
