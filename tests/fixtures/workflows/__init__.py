"""Workflow test fixtures."""

from .browser_workflow_guardrails import (
    ALIAS as BROWSER_GUARDRAIL_ALIAS,
    TARGET_URL as BROWSER_GUARDRAIL_TARGET_URL,
    create_browser_target_workspace,
    guarded_run_request,
    runtime_prerequisite,
    runtime_readiness_check,
    target_environment,
)
from .live_write_readiness import create_live_write_readiness_workspace, old_checked_at, save_ready_snapshot
from .side_effect_contract_alignment import (
    blocked_write_last_run,
    conflicting_policy,
    create_write_policy_workspace,
    legacy_rules_policy,
    supported_side_effect_contract,
    supersede_review_payload,
    unsupported_dom_last_run,
)

__all__ = [
    "BROWSER_GUARDRAIL_ALIAS",
    "BROWSER_GUARDRAIL_TARGET_URL",
    "create_browser_target_workspace",
    "create_live_write_readiness_workspace",
    "blocked_write_last_run",
    "conflicting_policy",
    "create_write_policy_workspace",
    "guarded_run_request",
    "legacy_rules_policy",
    "old_checked_at",
    "runtime_prerequisite",
    "runtime_readiness_check",
    "save_ready_snapshot",
    "supported_side_effect_contract",
    "supersede_review_payload",
    "target_environment",
    "unsupported_dom_last_run",
]
