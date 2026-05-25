from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workflows import engine
from proofsignal_spec.workflows.models import WORKFLOW_ID
from proofsignal_spec.workflows.prerequisites import check_prerequisites


def run_workflow(project: Path, workflow_id: str, goal: str, alias: str | None = None, integration: str | None = None) -> dict[str, Any]:
    if workflow_id != WORKFLOW_ID:
        raise ValueError(f"Unsupported workflow: {workflow_id}")
    run = engine.create_workflow_run(project, goal=goal, alias=alias, integration=integration)
    return run.to_dict()


def resume(project: Path, run_id: str) -> dict[str, Any]:
    return engine.resume_workflow(project, run_id).to_dict()


def status(project: Path, run_id: str | None = None) -> dict[str, Any]:
    return engine.workflow_status(project, run_id)


def list_runs(project: Path) -> dict[str, Any]:
    return engine.workflow_list(project)


def info(project: Path, workflow_id: str = WORKFLOW_ID, integration: str | None = None) -> dict[str, Any]:
    return engine.workflow_info(project, workflow_id, integration=integration)


def check(project: Path, stage: str, alias: str | None = None, refresh_decision: str | None = None) -> dict[str, Any]:
    return check_prerequisites(project, stage, alias=alias, refresh_decision=refresh_decision)
