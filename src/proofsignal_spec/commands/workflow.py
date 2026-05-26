from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workflows import engine
from proofsignal_spec.workflows import migration as workflow_migration
from proofsignal_spec.workflows import readiness as workflow_readiness
from proofsignal_spec.workflows import stage_persistence
from proofsignal_spec.workflows.models import WORKFLOW_ID
from proofsignal_spec.workflows.prerequisites import check_prerequisites


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


def migrate(project: Path, migration_id: str) -> dict[str, Any]:
    return workflow_migration.apply_migration(project, migration_id)
