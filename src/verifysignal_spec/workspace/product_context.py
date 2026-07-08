from __future__ import annotations

from pathlib import Path
from typing import Any

from . import layout
from .repository import load_document, now_iso, save_document
from .sensitive_files import filter_safe_paths
from .validation import validate_no_secret_values


def load_product_context(project: Path) -> dict[str, Any]:
    return load_document(layout.product_context_path(project), default={}) or {}


def save_product_context(project: Path, context: dict[str, Any]) -> None:
    context.setdefault("schemaVersion", "verifysignal-spec-product-context/v1")
    findings = validate_no_secret_values(context, layout.PRODUCT_CONTEXT_FILE)
    if findings:
        first = findings[0]
        raise ValueError(f"Secret-looking product context value at {first.get('path')}: {first.get('message')}")
    save_document(layout.product_context_path(project), context)


def summarize_safe_inspection(project: Path, candidate_paths: list[str]) -> dict[str, list[str]]:
    context = load_product_context(project)
    patterns = context.get("sensitivePathPatterns") or None
    safe, blocked = filter_safe_paths(candidate_paths, patterns)
    return {"safeInspectionPaths": safe, "blockedSensitivePaths": blocked}


def append_validation_goal(project: Path, goal: str) -> None:
    context = load_product_context(project)
    goals = list(context.get("validationGoals", []))
    if goal not in goals:
        goals.append(goal)
    context["validationGoals"] = goals
    save_product_context(project, context)


def understanding_metadata(context: dict[str, Any]) -> dict[str, Any]:
    metadata = context.get("understanding")
    if not isinstance(metadata, dict):
        metadata = {}
        context["understanding"] = metadata
    return metadata


def save_understanding_metadata(
    project: Path,
    context: dict[str, Any],
    *,
    generated_at: str,
    generated_git_hash: str | None,
    git_available: bool,
    stale_reasons: list[str] | None = None,
) -> None:
    metadata = understanding_metadata(context)
    metadata.update(
        {
            "generatedAt": generated_at,
            "generatedGitHash": generated_git_hash,
            "gitAvailable": git_available,
            "staleReasons": stale_reasons or [],
        }
    )
    save_product_context(project, context)


def update_understanding_stale_reasons(project: Path, stale_reasons: list[str]) -> dict[str, Any]:
    context = load_product_context(project)
    metadata = understanding_metadata(context)
    metadata["staleReasons"] = stale_reasons
    save_product_context(project, context)
    return context


def record_understanding_refresh_decision(
    project: Path,
    decision: str,
    stale_reasons: list[dict[str, Any]] | list[str],
    *,
    stage: str,
) -> dict[str, Any]:
    if decision not in {"accepted", "declined"}:
        raise ValueError("Refresh decision must be accepted or declined.")
    context = load_product_context(project)
    metadata = understanding_metadata(context)
    reason_codes: list[str] = []
    for item in stale_reasons:
        code = item.get("code") if isinstance(item, dict) else item
        if code:
            reason_codes.append(str(code))
    decided_at = now_iso()
    metadata["refreshDecision"] = {
        "decision": decision,
        "decidedAt": decided_at,
        "staleReasons": reason_codes,
        "stage": stage,
    }
    if decision == "declined":
        metadata["refreshDeclinedAt"] = decided_at
        metadata["refreshDeclinedReasons"] = reason_codes
    else:
        metadata["refreshAcceptedAt"] = decided_at
        metadata["refreshAcceptedReasons"] = reason_codes
    save_product_context(project, context)
    return metadata["refreshDecision"]


def persist_understanding_context(
    project: Path,
    *,
    repository_summary: str,
    local_start_instructions: str,
    coverage_inventory: dict[str, Any],
    candidate_use_cases: list[dict[str, Any]],
    generated_at: str,
    generated_git_hash: str | None,
    git_available: bool,
    safe_inspection_paths: list[str] | None = None,
    blocked_sensitive_paths: list[str] | None = None,
    runtime_requirements: list[str] | None = None,
) -> dict[str, Any]:
    context = load_product_context(project)
    context.update(
        {
            "repositorySummary": repository_summary,
            "localStartInstructions": local_start_instructions,
            "safeInspectionPaths": safe_inspection_paths or context.get("safeInspectionPaths", []),
            "blockedSensitivePaths": blocked_sensitive_paths or context.get("blockedSensitivePaths", []),
            "knownRuntimeRequirements": runtime_requirements or context.get("knownRuntimeRequirements", []),
            "coverageInventory": coverage_inventory,
            "candidateUseCases": candidate_use_cases,
        }
    )
    metadata = understanding_metadata(context)
    metadata.update(
        {
            "generatedAt": generated_at,
            "generatedGitHash": generated_git_hash,
            "gitAvailable": git_available,
            "staleReasons": [],
            "inventoryStatus": coverage_inventory.get("status"),
        }
    )
    save_product_context(project, context)
    return context
