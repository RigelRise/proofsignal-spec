from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.models import UseCaseRecord
from proofsignal_spec.workspace.repository import (
    create_default_use_case,
    load_document,
    load_registry,
    load_use_case,
    now_iso,
    save_document,
    save_use_case,
    update_use_case_workflow_reference,
)
from proofsignal_spec.workspace.validation import validate_no_secret_values

from .models import (
    WORKFLOW_ARTIFACT_PLAN_SCHEMA,
    WORKFLOW_ID,
    WORKFLOW_RUN_SCHEMA,
    WORKFLOW_STATE_SCHEMA,
    ArtifactPlan,
    AuthoringTaskSet,
    UseCaseWorkflowReference,
    WorkflowRun,
    WorkflowStageState,
)


def _reject_secrets(data: Any) -> None:
    findings = validate_no_secret_values(data)
    if findings:
        first = findings[0]
        raise ValueError(f"Secret-looking workflow value at {first.get('path')}: {first.get('message')}")


def project_relative(project: Path, path: Path) -> str:
    return layout.to_project_relative(project, path)


def workflow_dir_rel(project: Path, alias: str) -> str:
    return project_relative(project, layout.workflow_use_case_dir(project, alias))


def ensure_workflow_workspace(project: Path, alias: str | None = None) -> None:
    for directory in layout.workspace_dirs(project):
        directory.mkdir(parents=True, exist_ok=True)
    if alias:
        layout.workflow_use_case_dir(project, alias).mkdir(parents=True, exist_ok=True)


def create_stage_states(project: Path, alias: str) -> list[WorkflowStageState]:
    return [
        WorkflowStageState(stage="understand", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "understand"))),
        WorkflowStageState(stage="specify", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "specify"))),
        WorkflowStageState(stage="clarify", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "clarify"))),
        WorkflowStageState(stage="plan", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "plan"))),
        WorkflowStageState(stage="tasks", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "tasks"))),
        WorkflowStageState(stage="implement", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "implement"))),
        WorkflowStageState(stage="validate", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "validate"))),
        WorkflowStageState(stage="run", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "run"))),
        WorkflowStageState(stage="repair", documentPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "repair"))),
    ]


def state_document(project: Path, alias: str, run: WorkflowRun | None = None, current_stage: str = "understand", status: str = "paused") -> dict[str, Any]:
    states = run.stageStates if run else create_stage_states(project, alias)
    documents = {
        "understanding": project_relative(project, layout.workflow_stage_document_path(project, alias, "understand")),
        "spec": project_relative(project, layout.workflow_stage_document_path(project, alias, "specify")),
        "clarifications": project_relative(project, layout.workflow_stage_document_path(project, alias, "clarify")),
        "plan": project_relative(project, layout.workflow_stage_document_path(project, alias, "plan")),
        "tasks": project_relative(project, layout.workflow_stage_document_path(project, alias, "tasks")),
    }
    return {
        "schemaVersion": WORKFLOW_STATE_SCHEMA,
        "useCaseAlias": alias,
        "workflowId": WORKFLOW_ID,
        "currentStage": current_stage,
        "status": status,
        "documents": documents,
        "stageStates": [item.to_dict() for item in states],
        "nextCommand": run.nextCommand if run else f"/proofsignal-{current_stage} {alias}",
        "updatedAt": now_iso(),
    }


def save_workflow_state(project: Path, alias: str, data: dict[str, Any]) -> None:
    layout.ensure_path_safe_alias(alias)
    _reject_secrets(data)
    save_document(layout.workflow_state_path(project, alias), data)


def load_workflow_state(project: Path, alias: str) -> dict[str, Any]:
    return load_document(layout.workflow_state_path(project, alias), default={}) or {}


def save_workflow_run(project: Path, run: WorkflowRun) -> None:
    run.updatedAt = now_iso()
    _reject_secrets(run.to_dict())
    save_document(layout.workflow_run_path(project, run.runId), run.to_dict())


def load_workflow_run(project: Path, run_id: str) -> WorkflowRun:
    data = load_document(layout.workflow_run_path(project, run_id))
    if not data:
        raise FileNotFoundError(f"Workflow run not found: {run_id}")
    if data.get("schemaVersion") and data.get("schemaVersion") != WORKFLOW_RUN_SCHEMA:
        raise ValueError(f"Unsupported workflow run schema: {data.get('schemaVersion')}")
    return WorkflowRun.from_dict(data)


def list_workflow_runs(project: Path) -> list[WorkflowRun]:
    runs: list[WorkflowRun] = []
    directory = layout.workflow_runs_dir(project)
    if not directory.exists():
        return runs
    for path in sorted(directory.glob("*.yaml")):
        data = load_document(path)
        if data:
            runs.append(WorkflowRun.from_dict(data))
    runs.sort(key=lambda item: item.updatedAt or item.startedAt or "", reverse=True)
    return runs


def create_or_load_use_case(project: Path, alias: str, goal: str) -> UseCaseRecord:
    try:
        return load_use_case(project, alias)
    except FileNotFoundError:
        record = create_default_use_case(project, alias, goal)
        record.status = "draft"
        record.runRequest = None
        record.mainSkill = None
        record.skills = []
        save_use_case(project, record)
        return record


def link_workflow_reference(project: Path, alias: str, run: WorkflowRun, status: str = "paused") -> UseCaseRecord:
    reference = UseCaseWorkflowReference(
        workflowDir=workflow_dir_rel(project, alias),
        currentStage=run.currentStage,
        workflowStatus=status,
        lastWorkflowRunId=run.runId,
        lastUpdatedAt=now_iso(),
    )
    return update_use_case_workflow_reference(project, alias, reference.to_dict())


def import_legacy_use_case(project: Path, alias: str, run_id: str | None = None) -> dict[str, Any]:
    record = load_use_case(project, alias)
    ensure_workflow_workspace(project, alias)
    run = WorkflowRun(
        runId=run_id or f"wf-import-{alias}",
        useCaseAlias=alias,
        status="paused",
        currentStage="validate" if record.runRequest and record.mainSkill else "plan",
        workflowDir=workflow_dir_rel(project, alias),
        startedAt=now_iso(),
        updatedAt=now_iso(),
        stageStates=create_stage_states(project, alias),
        nextCommand=f"/proofsignal-{('validate' if record.runRequest and record.mainSkill else 'plan')} {alias}",
    )
    save_workflow_run(project, run)
    save_workflow_state(project, alias, state_document(project, alias, run, run.currentStage, run.status))
    link_workflow_reference(project, alias, run, run.status)
    return {"alias": alias, "runId": run.runId, "currentStage": run.currentStage}


def save_artifact_plan(project: Path, plan: ArtifactPlan) -> None:
    _reject_secrets(plan.to_dict())
    save_document(layout.workflow_stage_document_path(project, plan.useCaseAlias, "plan").with_suffix(".yaml"), plan.to_dict())


def load_artifact_plan(project: Path, alias: str) -> ArtifactPlan:
    data = load_document(layout.workflow_stage_document_path(project, alias, "plan").with_suffix(".yaml"))
    if not data:
        raise FileNotFoundError(f"Artifact plan not found for {alias}")
    if data.get("schemaVersion") and data.get("schemaVersion") != WORKFLOW_ARTIFACT_PLAN_SCHEMA:
        raise ValueError(f"Unsupported artifact plan schema: {data.get('schemaVersion')}")
    return ArtifactPlan.from_dict(data)


def save_task_set(project: Path, task_set: AuthoringTaskSet) -> None:
    _reject_secrets(task_set.to_dict())
    save_document(layout.workflow_stage_document_path(project, task_set.useCaseAlias, "tasks").with_suffix(".yaml"), task_set.to_dict())


def fingerprint_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def index_skill_reuse(project: Path) -> dict[str, list[dict[str, str]]]:
    index: dict[str, list[dict[str, str]]] = {}
    for item in load_registry(project).get("useCases", []):
        alias = item.get("alias")
        if not alias:
            continue
        try:
            record = load_use_case(project, alias)
        except Exception:
            continue
        for skill in record.skills:
            index.setdefault(skill.path, []).append({"useCaseAlias": alias, "runRequest": record.runRequest.path if record.runRequest else ""})
    return index
