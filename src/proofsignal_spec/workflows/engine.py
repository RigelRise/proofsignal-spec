from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from proofsignal_spec.commands import list as list_command
from proofsignal_spec.commands import repair as repair_command
from proofsignal_spec.commands import run as run_command
from proofsignal_spec.commands import validate as validate_command
from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.models import ArtifactReference
from proofsignal_spec.workspace.repository import load_document, load_use_case, now_iso, save_use_case

from .definitions import load_workflow_definition
from .browser_authoring import browser_authoring_contract
from .stage_contracts import stage_contracts_payload
from .models import WORKFLOW_ID, WORKFLOW_STAGES, ArtifactPlan, WorkflowRun, native_invocation
from .repository import (
    create_or_load_use_case,
    create_stage_states,
    ensure_workflow_workspace,
    import_legacy_use_case,
    link_workflow_reference,
    list_workflow_runs,
    load_artifact_plan,
    load_workflow_run,
    load_workflow_state,
    project_relative,
    save_artifact_plan,
    save_workflow_run,
    save_workflow_state,
    state_document,
    workflow_dir_rel,
)
from .stage_documents import write_artifact_plan, write_clarifications, write_handoff, write_specification, write_validation_summary
from .stages import initialize_understanding
from .tasks import generate_authoring_tasks
from .stage_documents import write_task_set
from .repository import save_task_set


def slug_from_goal(goal: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", goal.lower()).strip("-")
    return (slug[:40].strip("-") or "use-case")


def choose_integration(project: Path, requested: str | None = None) -> str:
    if requested:
        return requested
    from proofsignal_spec.integrations.manifests import load_all_states

    states = load_all_states(project).get("integrations", {})
    for key, value in states.items():
        if isinstance(value, dict) and value.get("default"):
            return key
    return "codex"


def next_command(stage: str, alias: str, integration: str | None = None) -> str:
    invocation = native_invocation(stage, "skill")
    return f"{invocation} {alias}".strip()


def create_workflow_run(project: Path, goal: str, alias: str | None = None, integration: str | None = None) -> WorkflowRun:
    alias = layout.ensure_path_safe_alias(alias or slug_from_goal(goal))
    integration = choose_integration(project, integration)
    ensure_workflow_workspace(project, alias)
    create_or_load_use_case(project, alias, goal)
    initialized = initialize_understanding(project, alias, goal)
    run_id = f"wf-{now_iso().replace('-', '').replace(':', '').replace('Z', '').replace('T', '-')}-{alias}"
    run = WorkflowRun(
        runId=run_id,
        useCaseAlias=alias,
        integration=integration,
        status="paused",
        currentStage="understand",
        startedAt=now_iso(),
        updatedAt=now_iso(),
        workflowDir=workflow_dir_rel(project, alias),
        stageStates=create_stage_states(project, alias),
        nextCommand=next_command("understand", alias, integration),
        resumeCommand=f"proofsignal workflow resume {run_id}",
    )
    run.stageStates[0].status = "completed"
    run.stageStates[0].completedAt = now_iso()
    run.stageStates[0].handoffSummary = "Repository understanding initialized."
    save_workflow_run(project, run)
    save_workflow_state(project, alias, state_document(project, alias, run, run.currentStage, run.status))
    link_workflow_reference(project, alias, run, run.status)
    return run


def resume_workflow(project: Path, run_id: str) -> WorkflowRun:
    run = load_workflow_run(project, run_id)
    if run.status in {"completed", "failed"}:
        return run
    run.status = "paused"
    run.resumeCommand = f"proofsignal workflow resume {run.runId}"
    if not run.nextCommand:
        run.nextCommand = next_command(run.currentStage, run.useCaseAlias, run.integration)
    save_workflow_run(project, run)
    return run


def workflow_status(project: Path, run_id: str | None = None) -> dict[str, Any]:
    run = load_workflow_run(project, run_id) if run_id else (list_workflow_runs(project)[0] if list_workflow_runs(project) else None)
    if not run:
        return {"schemaVersion": "proofsignal-spec-workflow-status/v1", "status": "not-started", "runs": []}
    state = load_workflow_state(project, run.useCaseAlias)
    return {
        "schemaVersion": "proofsignal-spec-workflow-status/v1",
        "runId": run.runId,
        "workflowId": run.workflowId,
        "useCaseAlias": run.useCaseAlias,
        "status": run.status,
        "currentStage": run.currentStage,
        "integration": run.integration,
        "workflowDir": run.workflowDir,
        "nextCommand": run.nextCommand,
        "resumeCommand": run.resumeCommand,
        "stageStates": [item.to_dict() for item in run.stageStates],
        "state": state,
    }


def workflow_status_for_alias(project: Path, alias: str) -> dict[str, Any]:
    alias = layout.ensure_path_safe_alias(alias)
    record = load_use_case(project, alias)
    state = load_workflow_state(project, alias)
    workflow = record.workflow or {}
    run_id = workflow.get("lastWorkflowRunId")
    if run_id:
        try:
            return workflow_status(project, str(run_id))
        except FileNotFoundError:
            pass
    return {
        "schemaVersion": "proofsignal-spec-workflow-status/v1",
        "useCaseAlias": alias,
        "status": state.get("status") or workflow.get("workflowStatus") or record.status,
        "currentStage": state.get("currentStage") or workflow.get("currentStage"),
        "workflowDir": workflow.get("workflowDir") or workflow_dir_rel(project, alias),
        "nextCommand": state.get("nextCommand"),
        "state": state,
    }


def workflow_show(project: Path, alias: str) -> dict[str, Any]:
    alias = layout.ensure_path_safe_alias(alias)
    record = load_use_case(project, alias)
    state = load_workflow_state(project, alias)
    documents = {
        stage: _workflow_document(project, alias, stage)
        for stage in ["understand", "specify", "clarify", "plan", "tasks", "implement", "validate", "run", "repair"]
    }
    artifact_plan = load_document(layout.workflow_stage_document_path(project, alias, "plan").with_suffix(".yaml"), default={}) or {}
    task_set = load_document(layout.workflow_stage_document_path(project, alias, "tasks").with_suffix(".yaml"), default={}) or {}
    return {
        "schemaVersion": "proofsignal-spec-workflow-show/v1",
        "useCaseAlias": alias,
        "status": state.get("status") or record.status,
        "currentStage": state.get("currentStage") or (record.workflow or {}).get("currentStage"),
        "useCase": record.to_dict(),
        "workflowState": state,
        "documents": documents,
        "artifactPlan": artifact_plan,
        "taskSet": task_set,
    }


def _workflow_document(project: Path, alias: str, stage: str) -> dict[str, Any]:
    path = layout.workflow_stage_document_path(project, alias, stage)
    if not path.exists():
        return {"path": project_relative(project, path), "exists": False}
    return {
        "path": project_relative(project, path),
        "exists": True,
        "content": path.read_text(encoding="utf-8"),
    }


def workflow_list(project: Path) -> dict[str, Any]:
    return {
        "schemaVersion": "proofsignal-spec-workflow-list/v1",
        "runs": [
            {
                "runId": run.runId,
                "workflowId": run.workflowId,
                "useCaseAlias": run.useCaseAlias,
                "status": run.status,
                "currentStage": run.currentStage,
                "integration": run.integration,
                "updatedAt": run.updatedAt,
            }
            for run in list_workflow_runs(project)
        ],
    }


def workflow_info(project: Path, workflow_id: str = WORKFLOW_ID, integration: str | None = None) -> dict[str, Any]:
    definition = load_workflow_definition(project, workflow_id)
    integration = choose_integration(project, integration)
    return {
        "schemaVersion": "proofsignal-spec-workflow-info/v1",
        "workflowId": definition.workflowId,
        "name": definition.name,
        "version": definition.version,
        "stages": definition.stages,
        "gates": definition.gates,
        "supportedIntegrations": ["codex", "claude"],
        "nativeCommands": {stage: native_invocation(stage, "skill") for stage in [*WORKFLOW_STAGES, "list"]},
        "stagePayloadContracts": stage_contracts_payload(),
        "browserAuthoringContract": browser_authoring_contract(),
        "integration": integration,
    }


def specify(project: Path, alias: str, goal: str) -> dict[str, Any]:
    ensure_workflow_workspace(project, alias)
    create_or_load_use_case(project, alias, goal)
    write_specification(project, alias, goal)
    return {"alias": alias, "documentPath": project_relative(project, layout.workflow_stage_document_path(project, alias, "specify"))}


def clarify(project: Path, alias: str, questions: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    questions = questions or [{"prompt": "What target URL, credential group, and success evidence should this use case use?", "status": "pending"}]
    write_clarifications(project, alias, questions)
    return {"alias": alias, "questions": questions}


def plan_artifacts(project: Path, alias: str) -> ArtifactPlan:
    plan = ArtifactPlan(
        useCaseAlias=alias,
        runRequest=f".proofsignal/run-requests/{alias}.yaml",
        mainSkill=f".proofsignal/skills/{alias}.browser.md",
        supportingSkills=[],
        runtimeInputs=[{"name": "baseUrl", "kind": "parameter"}, {"name": "qa-user", "kind": "credential"}],
        validationGates=["authoring-check", "runtime-readiness"],
    )
    save_artifact_plan(project, plan)
    write_artifact_plan(project, plan)
    return plan


def generate_tasks(project: Path, alias: str) -> dict[str, Any]:
    plan = load_artifact_plan(project, alias)
    task_set = generate_authoring_tasks(project, plan)
    task_set.generatedAt = now_iso()
    save_task_set(project, task_set)
    write_task_set(project, task_set)
    return task_set.to_dict()


def implement_artifacts(project: Path, alias: str) -> dict[str, Any]:
    from proofsignal_spec.workspace import artifacts

    plan = load_artifact_plan(project, alias)
    record = load_use_case(project, alias)
    record.runRequest = ArtifactReference(path=plan.runRequest, kind="run-request", generated=True, id=f"request.{alias}", version="1.0.0")
    record.mainSkill = ArtifactReference(path=plan.mainSkill, kind="skill", generated=True, id=f"skill.{alias}", version="1.0.0")
    record.skills = [record.mainSkill, *[ArtifactReference(path=path, kind="skill", generated=True) for path in plan.supportingSkills]]
    record.status = "draft"
    artifacts.write_generated_artifacts(project, record)
    save_use_case(project, record)
    write_handoff(project, alias, "implement", "Draft artifacts were generated from the approved artifact plan. Validation is still required.")
    return {"alias": alias, "status": record.status, "runRequest": plan.runRequest, "skills": [skill.path for skill in record.skills]}


def validate_stage(project: Path, alias: str, core_cmd: str | None = None) -> dict[str, Any]:
    result = validate_command.run(project, alias, runtime_readiness=True, core_cmd=core_cmd)
    write_validation_summary(project, alias, result, stage="validate")
    return result


def run_stage(project: Path, alias: str, core_cmd: str | None = None, non_interactive: bool = True) -> dict[str, Any]:
    result = run_command.run(project, alias, interactive=not non_interactive, core_cmd=core_cmd)
    write_validation_summary(project, alias, result, stage="run")
    return result


def classify_repair_stage(finding: dict[str, Any]) -> str:
    text = " ".join(str(value).lower() for value in finding.values())
    if any(term in text for term in ["requirement", "expected", "product", "missing context"]):
        return "clarify"
    if any(term in text for term in ["skill reuse", "artifact plan", "wrong skill", "run request"]):
        return "plan"
    if "task" in text or "fingerprint" in text:
        return "tasks"
    return "implement"


def repair_stage(project: Path, alias: str, from_report: str | None = None, approve: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    result = repair_command.run(project, alias, from_report=from_report, approve=approve, core_cmd=core_cmd)
    findings = result.get("repair", {}).get("findings", [])
    revisit = classify_repair_stage(findings[0]) if findings else "implement"
    result["returnStage"] = revisit
    write_handoff(project, alias, "repair", f"Repair should revisit {revisit} before edits are approved.")
    return result


def non_ai_list(project: Path) -> dict[str, Any]:
    return list_command.run(project)
