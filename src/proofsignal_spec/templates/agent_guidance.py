from __future__ import annotations

BROWSER_TARGET_BEFORE_PLANNING = "Confirm the browser target environment before planning executable artifacts"
RUNTIME_READINESS_BOUNDARY = (
    "runtime readiness verifies target resolution, target reachability, required runtime prerequisites, "
    "and Core authoring readiness"
)
CONFIRMED_REPAIR_BOUNDARY = "Selector, flow, data, and coverage changes require confirmation"
PUBLIC_WORKFLOW_CONTRACT_BOUNDARY = (
    "Use the public workflow contract from `proofsignal-spec workflow info proofsignal-use-case --json` "
    "and `stagePayloadContracts`; Do not inspect installed package source to infer payload schemas"
)
