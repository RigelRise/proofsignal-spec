from __future__ import annotations

from pathlib import Path
from typing import Any

from . import layout
from .repository import load_document, save_document
from .sensitive_files import filter_safe_paths


def load_product_context(project: Path) -> dict[str, Any]:
    return load_document(layout.product_context_path(project), default={}) or {}


def save_product_context(project: Path, context: dict[str, Any]) -> None:
    context.setdefault("schemaVersion", "proofsignal-spec-product-context/v1")
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
