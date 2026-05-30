# Data Model: Golden Path Productization

## FirstRunCandidate

Represents a validation candidate discovered in the user's real project.

**Fields**

- `alias`: Stable use-case alias.
- `surface`: User-visible route, page, or flow surface.
- `behavior`: User-visible behavior to validate.
- `sourceInventoryItems`: Coverage inventory item IDs backing the candidate.
- `priority`: Existing candidate priority.
- `confidence`: Existing candidate confidence.
- `requiresEnvironment`: Whether runtime target details are required.
- `knownRuntimeRequirements`: Runtime requirements such as `baseUrl` or
  credential references.

**Validation rules**

- Must reference existing inventory items.
- Must not include credential values.
- Must not be ranked as first-run ready when unresolved credentials are present.

## FirstRunCandidateScore

Ranks candidates for the first golden-path run.

**Fields**

- `candidateAlias`: Candidate being scored.
- `rank`: 1-based rank.
- `score`: Integer score from 0 to 100.
- `lowSetupRisk`: Score contribution for low setup complexity.
- `reachableRealTarget`: Score contribution for real target reachability.
- `credentialRisk`: Penalty for unresolved credentials or auth requirements.
- `renderedEvidenceSimplicity`: Score contribution for simple visible evidence.
- `dataDependencyRisk`: Penalty for empty or volatile data requirements.
- `inventoryFreshness`: Score contribution for complete/non-stale inventory.
- `rationale`: Human-readable ranking explanation.
- `blockers`: Blocking reasons if the candidate cannot be recommended.

**Validation rules**

- A first-run recommendation requires a non-blocked top candidate.
- A candidate with unresolved credential values cannot be recommended as the top
  first-run candidate.
- A fake/demo target cannot contribute to `reachableRealTarget`.

## FirstRunRecommendation

The product-owned recommendation shown before the first run.

**Fields**

- `schemaVersion`: `proofsignal-spec-first-run-recommendation/v1`.
- `status`: `ready`, `blocked`, `skipped`, or `unavailable`.
- `recommendedCandidate`: Top candidate when ready.
- `rankedCandidates`: Ordered `FirstRunCandidateScore` entries.
- `recommendationText`: Strong user-facing recommendation.
- `acceptancePrompt`: Prompt asking the user to accept or skip.
- `skipMeaning`: Explanation that skip is not success or failure.
- `nextCommand`: Recommended command or agent action.
- `stageCards`: Agent-chat stage cards for recommendation display.

**State transitions**

- `unavailable` -> `blocked` when no target or inventory is ready.
- `blocked` -> `ready` after required target/inventory inputs are available.
- `ready` -> `accepted` is recorded in golden-path state when the user accepts.
- `ready` -> `skipped` when the user declines.

## AgentChatStageCard

The standard primary UX block for each first-run stage.

**Fields**

- `stageId`: Stable stage identifier.
- `title`: Short stage title.
- `statusMarker`: One of `[RECOMMENDED]`, `[ACCEPTED]`, `[RUNNING]`,
  `[PASS]`, `[REPAIR]`, `[SKIPPED]`, `[BLOCKED]`, or `[FAIL]`.
- `summary`: One-line outcome or progress summary.
- `whyItMatters`: Short explanation of product value.
- `primaryEvidence`: Evidence highlight, artifact path, gate summary, or report
  reference.
- `repairDetails`: Before/after repair details when repair occurred.
- `nextAction`: Immediate next action.
- `secondaryRefs`: Optional report, evidence, or workspace references.

**Validation rules**

- All first-run stage cards require `stageId`, `title`, `statusMarker`,
  `summary`, `whyItMatters`, `primaryEvidence`, and `nextAction`.
- `primaryEvidence` must summarize the strongest current evidence, rationale,
  blocker, or state signal for the card without relying on raw logs.
- `repairDetails` is required when `statusMarker` is `[REPAIR]`.
- Raw logs are not valid primary evidence.
- Stage cards must not include credential values, browser storage values, cookie
  values, or raw sensitive payloads.

## GoldenPathRunState

Tracks the user's first golden-path run.

**Fields**

- `useCaseAlias`: Accepted candidate alias.
- `target`: Confirmed real target locator, redacted when needed.
- `recommendationStatus`: `ready`, `accepted`, `skipped`, or `blocked`.
- `firstRunStatus`: `not-started`, `running`, `passed`, `repairing`,
  `repaired-passed`, `failed`, `blocked`, `incomplete`, or `skipped`.
- `strictPass`: Boolean.
- `coreBrowserStatus`: Public Core/browser status.
- `specCoverageStatus`: Spec gate coverage status.
- `missingRequiredGates`: Required gates not proven.
- `repairFeedback`: Repair feedback records when repair occurred.
- `stageCards`: Stage cards emitted during the journey.

**State transitions**

- `ready` -> `skipped` when the user declines the candidate.
- `accepted` -> `running` when execution starts.
- `running` -> `passed` when Core/browser passed and Spec coverage is complete.
- `running` -> `incomplete` when Core/browser passed but required Spec evidence
  is missing.
- `running` -> `repairing` when a repairable failure is classified.
- `repairing` -> `repaired-passed` after repair, revalidation, rerun, and strict
  pass.
- Any execution state -> `blocked` when target, credential, Core, or contract
  prerequisites cannot be resolved.

## RepairFeedback

Explains repair decisions in the first-run UX.

**Fields**

- `repairId`: Repair session identifier.
- `category`: Runtime or authoring category.
- `autonomy`: `auto-applied`, `confirmation-required`, or `blocked`.
- `safeMechanical`: Boolean.
- `before`: Summary of the failing artifact or behavior.
- `after`: Summary of the repaired artifact or behavior.
- `intentPreserved`: Boolean.
- `confirmationRequired`: Boolean.
- `confirmationRecord`: Confirmation reference when required.
- `revalidationStatus`: `passed`, `failed`, `not-run`, or `blocked`.
- `rerunStatus`: Final run status when rerun occurred.

**Validation rules**

- Auto-applied repairs must be safe mechanical repairs and must preserve
  validation intent.
- Repairs touching data assumptions, credentials, required gates, or expected
  product behavior require confirmation.
- Success after repair requires revalidation and rerun.
- Repair feedback must not include credential values, browser storage values,
  cookie values, or raw sensitive payloads.

## GoldenPathWorkspaceState

Represents project-local state created by the golden-path journey and the safe
inspection/reset boundary for that state.

**Fields**

- `schemaVersion`: `proofsignal-spec-golden-path-workspace-state/v1`.
- `status`: `ready`, `blocked`, `empty`, or `reset`.
- `projectRoot`: Target project root path, shown in redacted or normalized form
  when necessary.
- `firstRunState`: Current `GoldenPathRunState` summary.
- `ownedArtifacts`: Project-local artifacts created or updated by the golden
  path, including use-case records, run request, skills, run history,
  repair sessions, stage-card summaries, and generated guidance references.
- `preservedArtifacts`: Existing or unrelated `.proofsignal/` artifacts that
  must not be modified by a golden-path reset.
- `resetPreview`: Ordered list of changes a reset would apply.
- `resumeHint`: Next safe command when the user stopped midway through the
  journey.
- `warnings`: Non-blocking state warnings such as older schema versions, stale
  guidance, or missing owned artifacts.
- `nextAction`: Next CLI command or agent action.

**Validation rules**

- Inspect operations must be read-only.
- Reset operations must operate only on `ownedArtifacts` or golden-path state
  records and must preserve unrelated user-authored artifacts.
- Reset operations must provide a preview before applying destructive cleanup.
- Older workspace state must produce a recoverable warning or blocker instead of
  silent deletion.
