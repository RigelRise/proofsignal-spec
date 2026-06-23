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
PLAYWRIGHT_MCP_GUIDANCE = (
    "If you have a Playwright MCP server available (live browser tools such as `browser_navigate` and "
    "`browser_snapshot`), you MAY use it to author and repair browser selectors against the live page instead "
    "of guessing from source — but it is an authoring aid, never a validator: every selector it suggests must "
    "still be confirmed by `proofsignal discover` and the use case must still pass `proofsignal run`, and if the "
    "MCP and `discover` disagree, `discover` wins. Without a Playwright MCP, author from source as usual; the "
    "deterministic grounding and gate are unchanged. Never persist or print MCP snapshots, DOM, screenshots, "
    "cookies, or storage state. On authenticated surfaces load auth only from the environment or a "
    "developer-controlled `--storage-state` file (never written into `.proofsignal/`); on write surfaces let the "
    "MCP explore only up to the commit step and never cross it — only the deterministic `run` crosses the commit"
)
