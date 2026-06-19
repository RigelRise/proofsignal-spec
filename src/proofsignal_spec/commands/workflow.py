from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workflows import engine
from proofsignal_spec.workflows import migration as workflow_migration
from proofsignal_spec.workflows import readiness as workflow_readiness
from proofsignal_spec.workflows import stage_persistence
from proofsignal_spec.workflows.first_run import accept_first_run, build_first_run_recommendation, skip_first_run
from proofsignal_spec.workflows.repository import inspect_golden_path_workspace_state, reset_golden_path_workspace_state
from proofsignal_spec.workflows.models import WORKFLOW_ID
from proofsignal_spec.workflows.prerequisites import check_prerequisites
from proofsignal_spec.workspace.models import SupersedeReview
from proofsignal_spec.workspace.repository import now_iso, save_supersede_review
from proofsignal_spec.workspace.validation import validate_no_secret_values


def run_workflow(project: Path, workflow_id: str, goal: str, alias: str | None = None, integration: str | None = None) -> dict[str, Any]:
    if workflow_id != WORKFLOW_ID:
        raise ValueError(f"Unsupported workflow: {workflow_id}")
    run = engine.create_workflow_run(project, goal=goal, alias=alias, integration=integration)
    return run.to_dict()


def resume(project: Path, run_id: str) -> dict[str, Any]:
    return engine.resume_workflow(project, run_id).to_dict()


def status(project: Path, run_id: str | None = None, alias: str | None = None) -> dict[str, Any]:
    if run_id and alias:
        raise ValueError("Use workflow status with either a run_id or --alias, not both.")
    if alias:
        return engine.workflow_status_for_alias(project, alias)
    if run_id:
        try:
            return engine.workflow_status(project, run_id)
        except FileNotFoundError as original:
            try:
                return engine.workflow_status_for_alias(project, run_id)
            except FileNotFoundError:
                raise original
    return engine.workflow_status(project, run_id)


def show(project: Path, alias: str) -> dict[str, Any]:
    return engine.workflow_show(project, alias)


def list_runs(project: Path) -> dict[str, Any]:
    return engine.workflow_list(project)


def info(project: Path, workflow_id: str = WORKFLOW_ID, integration: str | None = None) -> dict[str, Any]:
    return engine.workflow_info(project, workflow_id, integration=integration)


def check(project: Path, stage: str, alias: str | None = None, refresh_decision: str | None = None) -> dict[str, Any]:
    if stage == "validate":
        return workflow_readiness.validation_readiness(project, alias=alias)
    return check_prerequisites(project, stage, alias=alias, refresh_decision=refresh_decision)


def persist(project: Path, stage: str, alias: str | None = None, scope: str | None = None, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return stage_persistence.persist_stage(project, stage, alias=alias, scope=scope, payload=payload)


def supersede_write_outcome(project: Path, alias: str, payload: dict[str, Any]) -> dict[str, Any]:
    review_data = dict(payload)
    review_data.setdefault("createdAt", now_iso())
    review = SupersedeReview.from_dict(review_data)
    findings = [*review.validate(), *validate_no_secret_values(review.to_dict(), "supersedeReview")]
    blockers = [item for item in findings if item.get("severity") == "blocking"]
    if blockers:
        return {
            "schemaVersion": "proofsignal-spec-supersede-review-result/v1",
            "alias": alias,
            "status": "blocked",
            "blockers": blockers,
        }
    saved = save_supersede_review(project, alias, review)
    return {
        "schemaVersion": "proofsignal-spec-supersede-review-result/v1",
        "alias": alias,
        "status": "persisted",
        "review": saved.to_dict(),
        "nextAction": f"proofsignal workflow check run --alias {alias} --json",
    }


def migrate(project: Path, migration_id: str) -> dict[str, Any]:
    return workflow_migration.apply_migration(project, migration_id)


def recommend_first_run(project: Path) -> dict[str, Any]:
    return build_first_run_recommendation(project).to_dict()


def accept_golden_path_first_run(project: Path, alias: str) -> dict[str, Any]:
    return accept_first_run(project, alias)


def skip_golden_path_first_run(project: Path) -> dict[str, Any]:
    return skip_first_run(project)


def inspect_golden_path_state(project: Path) -> dict[str, Any]:
    return inspect_golden_path_workspace_state(project)


def reset_golden_path_state(project: Path, *, preview: bool = False, confirm: bool = False) -> dict[str, Any]:
    return reset_golden_path_workspace_state(project, preview=preview, confirm=confirm)
