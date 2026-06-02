from __future__ import annotations

BROWSER_TARGET_BEFORE_PLANNING = "Confirm the browser target environment before planning executable artifacts"
RUNTIME_READINESS_BOUNDARY = (
    "runtime readiness verifies target resolution, target reachability, required runtime prerequisites, "
    "and Core authoring readiness"
)
CONFIRMED_REPAIR_BOUNDARY = "Selector, flow, data, and coverage changes require confirmation"
SAFE_MECHANICAL_REPAIR_GUIDANCE = (
    "Safe mechanical selector, wait, step-ordering, target-specificity, equivalent-flow, and run-profile repairs may auto-apply only when validation intent is preserved; "
    "data, credential, required-gate, target-selection, and expected-behavior changes still require confirmation"
)
FIRST_RUN_STAGE_CARD_GUIDANCE = (
    "For Golden Path first-run output, render clear stage cards with a separator, status marker, "
    "one-line summary, why it matters, primary evidence, repair details when present, and next action"
)
REAL_TARGET_FIRST_RECOMMENDATION = (
    "Recommend the simplest stable real-target validation as the first run and state that accepting it is highly recommended; "
    "do not use fake/demo targets as a user-facing fallback"
)
MISSING_UNDERSTANDING_AUTO_PREPARE = (
    "When specify reports missing repository understanding with auto-prepare metadata, run safe understanding, avoid sensitive files, "
    "then resume the original specify flow without requiring the user to manually restart"
)
PUBLIC_WORKFLOW_CONTRACT_BOUNDARY = (
    "Use the public workflow contract from `proofsignal workflow info proofsignal-use-case --json` "
    "and `stagePayloadContracts`; Do not inspect installed package source to infer payload schemas"
)
