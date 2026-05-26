from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace import artifacts, layout
from proofsignal_spec.workspace.models import ArtifactReference, AuthoringQuestion, RuntimeInputRequirement
from proofsignal_spec.workspace.product_context import load_product_context, save_product_context
from proofsignal_spec.workspace.repository import init_workspace, load_use_case, now_iso, save_use_case
from proofsignal_spec.workspace.validation import validate_no_secret_values

from .coverage_inventory import candidate_dicts, merge_inventory, normalize_scope
from .browser_authoring import validate_browser_payload
from .models import (
    WORKFLOW_STAGES,
    ArtifactPlan,
    AuthoringTask,
    AuthoringTaskSet,
    ManagedWorkspaceArtifact,
    ReadinessBlocker,
    StagePersistenceResult,
)
from .prerequisites import current_git_hash
from .repository import (
    create_or_load_use_case,
    ensure_workflow_workspace,
    fingerprint_text,
    project_relative,
    load_artifact_plan,
    save_artifact_plan,
    save_task_set,
    save_workflow_state,
    state_document,
)
from .stage_documents import (
    write_artifact_plan,
    write_clarifications,
    write_global_understanding,
    write_handoff,
    write_specification,
    write_task_set,
)

PERSISTABLE_STAGES = {"understand", "specify", "clarify", "plan", "tasks", "implement"}
BLOCKING_CLARIFICATION_AREAS = {"runtime", "data", "credential", "credentials", "permission", "permissions", "outcome", "expectedOutcome"}


def persist_stage(
    project: Path,
    stage: str,
    *,
    alias: str | None = None,
    scope: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if stage not in PERSISTABLE_STAGES:
        return _blocked(
            stage,
            alias,
            code="stage.unsupported",
            message=f"Stage {stage} cannot be persisted. Supported stages: {', '.join(sorted(PERSISTABLE_STAGES))}.",
            invalid=True,
        )
    try:
        normalized_scope = normalize_scope(scope)
    except ValueError as exc:
        return _blocked(stage, alias, code="scope.invalid", message=str(exc), invalid=True)

    content = _payload_content(payload or {})
    resolved_alias = alias or content.get("alias")
    findings = validate_no_secret_values(content)
    if findings:
        first = findings[0]
        return _blocked(
            stage,
            resolved_alias,
            code="payload.secret-looking-value",
            message=f"Secret-looking value must not be persisted at {first.get('path')}.",
            invalid=True,
        )

    project = project.resolve()
    init_workspace(project)
    try:
        if stage == "understand":
            result = _persist_understanding(project, content, normalized_scope)
        elif stage == "specify":
            result = _persist_specification(project, str(resolved_alias or ""), content)
        elif stage == "clarify":
            result = _persist_clarifications(project, str(resolved_alias or ""), content)
        elif stage == "plan":
            result = _persist_plan(project, str(resolved_alias or ""), content)
        elif stage == "tasks":
            result = _persist_tasks(project, str(resolved_alias or ""), content)
        else:
            result = _persist_implementation(project, str(resolved_alias or ""), content)
    except ValueError as exc:
        return _blocked(stage, resolved_alias, code="payload.invalid", message=str(exc), invalid=True)
    except FileNotFoundError as exc:
        return _blocked(stage, resolved_alias, code="workspace.missing", message=str(exc))
    return result.to_dict()


def unresolved_blocking_questions(project: Path, alias: str) -> list[dict[str, Any]]:
    try:
        record = load_use_case(project, alias)
    except FileNotFoundError:
        return []
    blockers: list[dict[str, Any]] = []
    for question in record.authoringQuestions:
        if question.status == "answered":
            continue
        affected = f"{question.affects or ''} {question.reason}".lower()
        if any(area.lower() in affected for area in BLOCKING_CLARIFICATION_AREAS):
            blockers.append(question.to_dict())
    return blockers


def _persist_understanding(project: Path, content: dict[str, Any], scope: str) -> StagePersistenceResult:
    content = _normalize_understanding_content(content)
    _require_fields(content, ["repositorySummary", "localStartInstructions", "coverageInventory"])
    context = load_product_context(project)
    existing_inventory = context.get("coverageInventory")
    inventory = merge_inventory(existing_inventory, content.get("coverageInventory"), scope=scope)
    generated_at = inventory.generatedAt or now_iso()
    generated_git_hash = content.get("generatedGitHash") or inventory.generatedGitHash or current_git_hash(project)
    git_available = bool(generated_git_hash) or bool(content.get("gitAvailable"))

    context.update(
        {
            "repositorySummary": content["repositorySummary"],
            "localStartInstructions": content["localStartInstructions"],
            "safeInspectionPaths": content.get("safeInspectionPaths", context.get("safeInspectionPaths", [])),
            "blockedSensitivePaths": content.get("blockedSensitivePaths", context.get("blockedSensitivePaths", [])),
            "validationGoals": content.get("validationGoals", context.get("validationGoals", [])),
            "knownRuntimeRequirements": content.get("knownRuntimeRequirements", context.get("knownRuntimeRequirements", [])),
            "coverageInventory": inventory.to_dict(),
            "candidateUseCases": candidate_dicts(inventory),
            "understanding": {
                "generatedAt": generated_at,
                "generatedGitHash": generated_git_hash,
                "gitAvailable": git_available,
                "staleReasons": [],
                "inventoryStatus": inventory.status,
                "inventoryScope": scope,
                "recommendedFollowUpScope": _recommended_follow_up_scope(inventory.status, scope),
            },
        }
    )
    if not generated_git_hash and not content.get("gitUnavailableReason"):
        raise ValueError("Understanding payload requires generatedGitHash or gitUnavailableReason.")
    if content.get("gitUnavailableReason"):
        context["understanding"]["gitUnavailableReason"] = content.get("gitUnavailableReason")

    save_product_context(project, context)
    write_global_understanding(project, context)
    return StagePersistenceResult(
        stage="understand",
        status="persisted",
        writtenArtifacts=[
            _artifact(project, layout.product_context_path(project), "product-context"),
            _artifact(project, layout.workflow_global_understanding_path(project), "understanding"),
        ],
        updatedRecords=["product-context", "coverage-inventory"],
        warnings=_inventory_warnings(inventory.status),
        nextCommand="/proofsignal-specify",
    )


def _persist_specification(project: Path, alias: str, content: dict[str, Any]) -> StagePersistenceResult:
    alias = _alias(alias)
    content = _normalize_specification_content(project, alias, content)
    _require_fields(content, ["surface", "behavior", "expectedOutcome"])
    if not (content.get("sourceInventoryItems") or content.get("customSourceReason")):
        raise ValueError("Specification payload requires sourceInventoryItems or customSourceReason.")
    ensure_workflow_workspace(project, alias)
    goal = str(content["behavior"])
    record = create_or_load_use_case(project, alias, goal)
    record.title = content.get("title") or alias.replace("-", " ").title()
    record.description = goal
    record.targetSurface = str(content.get("surface") or "browser")
    record.status = "draft"
    save_use_case(project, record)
    runtime = [str(item) for item in content.get("runtimeAssumptions", [])]
    write_specification(project, alias, goal, runtime_assumptions=runtime)
    save_workflow_state(project, alias, state_document(project, alias, current_stage="clarify", status="paused"))
    return StagePersistenceResult(
        stage="specify",
        alias=alias,
        status="persisted",
        writtenArtifacts=[
            _artifact(project, layout.use_case_path(project, alias), "use-case"),
            _artifact(project, layout.workflow_stage_document_path(project, alias, "specify"), "specification"),
            _artifact(project, layout.workflow_state_path(project, alias), "workflow-state"),
            _artifact(project, layout.registry_path(project), "registry"),
        ],
        updatedRecords=[f"use-cases/{alias}", "registry"],
        nextCommand=f"/proofsignal-clarify {alias}",
    )


def _persist_clarifications(project: Path, alias: str, content: dict[str, Any]) -> StagePersistenceResult:
    alias = _alias(alias)
    record = load_use_case(project, alias)
    if "questions" not in content and not content.get("answers"):
        raise ValueError("Clarification payload requires questions or answers.")
    if "questions" in content:
        questions = [_question_from_dict(item) for item in content.get("questions", [])]
    else:
        questions = list(record.authoringQuestions)
    for answer in content.get("answers", []):
        _apply_answer(questions, answer)
    record.authoringQuestions = questions
    save_use_case(project, record)
    write_clarifications(project, alias, [question.to_dict() for question in questions])
    save_workflow_state(project, alias, state_document(project, alias, current_stage="plan", status="paused"))
    blockers = unresolved_blocking_questions(project, alias)
    warnings = ["Blocking environment-dependent questions remain unresolved."] if blockers else []
    return StagePersistenceResult(
        stage="clarify",
        alias=alias,
        status="persisted",
        writtenArtifacts=[
            _artifact(project, layout.use_case_path(project, alias), "use-case"),
            _artifact(project, layout.workflow_stage_document_path(project, alias, "clarify"), "clarifications"),
            _artifact(project, layout.workflow_state_path(project, alias), "workflow-state"),
            _artifact(project, layout.registry_path(project), "registry"),
        ],
        updatedRecords=[f"use-cases/{alias}", "registry"],
        warnings=warnings,
        nextCommand=f"/proofsignal-plan {alias}",
    )


def _persist_plan(project: Path, alias: str, content: dict[str, Any]) -> StagePersistenceResult:
    alias = _alias(alias)
    content = _normalize_plan_content(alias, content)
    blockers = content.get("unresolvedBlockingClarifications") or unresolved_blocking_questions(project, alias)
    if blockers:
        return StagePersistenceResult(
            stage="plan",
            alias=alias,
            status="blocked",
            blockers=[
                ReadinessBlocker(
                    code="clarification.unresolved-blocking",
                    message="Planning is blocked by unresolved runtime, data, credential, permission, or outcome clarifications.",
                    recoveryCommand=f"proofsignal-spec workflow persist clarify --alias {alias} --payload <answers.json> --json",
                )
            ],
            nextCommand=f"/proofsignal-clarify {alias}",
        )
    _require_fields(content, ["runRequest", "reusableSkills", "runtimeInputs"])
    run_request = _artifact_path(content["runRequest"], default=f".proofsignal/run-requests/{alias}.yaml")
    skill_paths = [_skill_path(item) for item in content.get("reusableSkills", [])]
    main_skill = _artifact_path(content.get("mainSkill") or (skill_paths[0] if skill_paths else f".proofsignal/skills/{alias}.browser.md"))
    supporting = [path for path in skill_paths if path != main_skill]
    plan = ArtifactPlan(
        useCaseAlias=alias,
        runRequest=run_request,
        mainSkill=main_skill,
        supportingSkills=supporting,
        skillReuse=list(content.get("skillReuse", [])),
        runtimeInputs=list(content.get("runtimeInputs", [])),
        preconditions=[str(item) for item in content.get("preconditions", [])],
        validationGates=[str(item) for item in content.get("validationGates", ["authoring-check", "runtime-readiness"])],
    )
    save_artifact_plan(project, plan)
    write_artifact_plan(project, plan)
    save_workflow_state(project, alias, state_document(project, alias, current_stage="tasks", status="paused"))
    return StagePersistenceResult(
        stage="plan",
        alias=alias,
        status="persisted",
        writtenArtifacts=[
            _artifact(project, layout.workflow_stage_document_path(project, alias, "plan"), "plan"),
            _artifact(project, layout.workflow_stage_document_path(project, alias, "plan").with_suffix(".yaml"), "artifact-plan"),
            _artifact(project, layout.workflow_state_path(project, alias), "workflow-state"),
        ],
        updatedRecords=[f"artifact-plans/{alias}"],
        nextCommand=f"/proofsignal-tasks {alias}",
    )


def _persist_tasks(project: Path, alias: str, content: dict[str, Any]) -> StagePersistenceResult:
    alias = _alias(alias)
    _require_fields(content, ["tasks"])
    tasks = [AuthoringTask.from_dict(item if isinstance(item, dict) else {"id": f"T{index + 1:03d}", "description": str(item)}) for index, item in enumerate(content.get("tasks", []))]
    task_set = AuthoringTaskSet(
        taskSetId=f"tasks.{alias}",
        useCaseAlias=alias,
        sourcePlanPath=project_relative(project, layout.workflow_stage_document_path(project, alias, "plan").with_suffix(".yaml")),
        planFingerprint=fingerprint_text(str(content.get("dependencies", "")) + str(content.get("parallelizableGroups", "")) + str([task.to_dict() for task in tasks])),
        generatedAt=now_iso(),
        tasks=tasks,
    )
    save_task_set(project, task_set)
    write_task_set(project, task_set)
    save_workflow_state(project, alias, state_document(project, alias, current_stage="implement", status="paused"))
    return StagePersistenceResult(
        stage="tasks",
        alias=alias,
        status="persisted",
        writtenArtifacts=[
            _artifact(project, layout.workflow_stage_document_path(project, alias, "tasks"), "tasks"),
            _artifact(project, layout.workflow_stage_document_path(project, alias, "tasks").with_suffix(".yaml"), "task-set"),
            _artifact(project, layout.workflow_state_path(project, alias), "workflow-state"),
        ],
        updatedRecords=[f"tasks/{alias}"],
        nextCommand=f"/proofsignal-implement {alias}",
    )


def _persist_implementation(project: Path, alias: str, content: dict[str, Any]) -> StagePersistenceResult:
    alias = _alias(alias)
    content = _normalize_implementation_content(alias, content)
    _require_fields(content, ["runRequest", "skills"])
    record = load_use_case(project, alias)
    run_request_path = _artifact_path(content["runRequest"], default=f".proofsignal/run-requests/{alias}.yaml")
    if not run_request_path.startswith(f"{layout.WORKSPACE_DIR}/{layout.RUN_REQUESTS_DIR}/"):
        raise ValueError("Generated run requests must be under .proofsignal/run-requests/.")
    skills = [_skill_reference(item) for item in content.get("skills", [])]
    if not skills:
        raise ValueError("Implementation requires at least one browser skill.")
    record.runRequest = ArtifactReference(path=run_request_path, kind="run-request", generated=True, id=f"request.{alias}", version="1.0.0")
    record.mainSkill = skills[0]
    record.skills = skills
    runtime_inputs = content.get("runtimeInputs") or _runtime_inputs_from_run_request_payload(content.get("runRequest")) or _planned_runtime_inputs(project, alias)
    content["runtimeInputs"] = runtime_inputs
    record.runtimeInputs = [_runtime_input(item) for item in runtime_inputs]
    record.status = "draft"

    run_request_content = _ensure_core_run_request_document(_artifact_content(content["runRequest"]), record, content)
    _write_payload_artifact(project, run_request_path, run_request_content, lambda: artifacts.render_run_request(record))
    for item, skill in zip(content.get("skills", []), skills, strict=False):
        skill_content = _ensure_core_skill_document(_artifact_content(item), record, skill, item)
        _write_payload_artifact(project, skill.path, skill_content, lambda record=record, skill=skill: artifacts.render_skill(record, skill))

    save_use_case(project, record)
    write_handoff(project, alias, "implement", "Draft canonical artifacts were persisted by proofsignal-spec workflow persist implement. Validation is still required.")
    save_workflow_state(project, alias, state_document(project, alias, current_stage="validate", status="paused"))
    return StagePersistenceResult(
        stage="implement",
        alias=alias,
        status="persisted",
        writtenArtifacts=[
            _artifact(project, layout.project_relative_path(project, run_request_path), "run-request"),
            *[_artifact(project, layout.project_relative_path(project, skill.path), "skill") for skill in skills],
            _artifact(project, layout.use_case_path(project, alias), "use-case"),
            _artifact(project, layout.registry_path(project), "registry"),
            _artifact(project, layout.workflow_stage_document_path(project, alias, "implement"), "handoff"),
            _artifact(project, layout.workflow_state_path(project, alias), "workflow-state"),
        ],
        updatedRecords=[f"use-cases/{alias}", "registry"],
        nextCommand=f"/proofsignal-validate {alias}",
    )


def _payload_content(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("payload") if isinstance(payload.get("payload"), dict) else payload
    return dict(data)


def _normalize_understanding_content(content: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(content)
    if "localStartInstructions" not in normalized and "startInstructions" in normalized:
        start = normalized["startInstructions"]
        if isinstance(start, dict):
            normalized["localStartInstructions"] = "; ".join(f"{key}: {value}" for key, value in start.items())
        else:
            normalized["localStartInstructions"] = str(start)
    if "safeInspectionPaths" not in normalized and "safePaths" in normalized:
        normalized["safeInspectionPaths"] = normalized["safePaths"]
    if "generatedGitHash" not in normalized:
        normalized["generatedGitHash"] = normalized.get("gitHash") or normalized.get("commitHash") or normalized.get("generatedCommitHash")
    inventory = dict(normalized.get("coverageInventory") or {})
    if normalized.get("candidateUseCases") and not inventory.get("candidateUseCases"):
        inventory["candidateUseCases"] = normalized["candidateUseCases"]
    if normalized.get("generatedGitHash") and not inventory.get("generatedGitHash"):
        inventory["generatedGitHash"] = normalized["generatedGitHash"]
    normalized["coverageInventory"] = inventory
    return normalized


def _normalize_specification_content(project: Path, alias: str, content: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(content)
    normalized.setdefault("surface", normalized.get("targetSurface") or normalized.get("route"))
    normalized.setdefault("behavior", normalized.get("purpose") or normalized.get("description") or normalized.get("intent"))
    if "expectedOutcome" not in normalized and "expectedOutcomes" in normalized:
        normalized["expectedOutcome"] = normalized["expectedOutcomes"]
    if not (normalized.get("sourceInventoryItems") or normalized.get("customSourceReason")):
        candidate = _candidate_from_context(project, alias)
        if candidate and candidate.get("sourceInventoryItems"):
            normalized["sourceInventoryItems"] = candidate["sourceInventoryItems"]
        else:
            normalized["customSourceReason"] = "Custom use case selected by developer during workflow specification."
    return normalized


def _candidate_from_context(project: Path, alias: str) -> dict[str, Any] | None:
    for candidate in load_product_context(project).get("candidateUseCases", []):
        if isinstance(candidate, dict) and (candidate.get("alias") == alias or candidate.get("candidateAlias") == alias):
            return candidate
    return None


def _normalize_plan_content(alias: str, content: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(content)
    if "reusableSkills" not in normalized and "skills" in normalized:
        normalized["reusableSkills"] = normalized["skills"]
    if "reusableSkills" not in normalized and "supportingSkills" in normalized:
        skills = []
        if normalized.get("mainSkill"):
            skills.append(normalized["mainSkill"])
        skills.extend(normalized.get("supportingSkills") or [])
        normalized["reusableSkills"] = skills
    if "runtimeInputs" not in normalized:
        run_request = normalized.get("runRequest")
        if isinstance(run_request, dict):
            intent = run_request.get("intent") if isinstance(run_request.get("intent"), dict) else {}
            normalized["runtimeInputs"] = (
                run_request.get("runtimeInputs")
                or intent.get("runtimeInputs")
                or _runtime_inputs_from_parameters(run_request.get("parameters", {}))
            )
    normalized.setdefault("runtimeInputs", [])
    normalized.setdefault("runRequest", f".proofsignal/run-requests/{alias}.yaml")
    return normalized


def _normalize_implementation_content(alias: str, content: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(content)
    artifacts_payload = normalized.get("artifacts")
    if isinstance(artifacts_payload, list):
        skills: list[dict[str, Any]] = []
        for artifact in artifacts_payload:
            if not isinstance(artifact, dict):
                continue
            kind = artifact.get("kind")
            path = str(artifact.get("path", ""))
            if kind == "run-request" or path.endswith(".yaml"):
                normalized.setdefault("runRequest", artifact)
            elif kind == "skill" or path.endswith(".browser.md"):
                skills.append(artifact)
        if skills and "skills" not in normalized:
            normalized["skills"] = skills
    normalized.setdefault("runRequest", {"path": f".proofsignal/run-requests/{alias}.yaml"})
    normalized.setdefault("skills", [])
    return normalized


def _alias(value: str) -> str:
    if not value:
        raise ValueError("Stage requires alias.")
    return layout.ensure_path_safe_alias(value)


def _require_fields(data: dict[str, Any], fields: list[str]) -> None:
    missing = []
    for field in fields:
        value = data.get(field)
        if field not in data or value is None or value == "":
            missing.append(field)
    if missing:
        raise ValueError(f"Payload missing required fields: {', '.join(missing)}.")


def _artifact_path(value: Any, *, default: str | None = None) -> str:
    if isinstance(value, dict):
        return str(value.get("path") or default or value.get("name") or "")
    return str(value or default or "")


def _skill_path(value: Any) -> str:
    path = _artifact_path(value)
    name = path
    if isinstance(value, dict):
        name = str(value.get("name") or value.get("id") or path)
    if not path or "/" not in path:
        safe = layout.ensure_path_safe_alias(name.replace("skill.", "").replace("_", "-").lower())
        path = f".proofsignal/skills/{safe}.browser.md"
    if not path.startswith(f"{layout.WORKSPACE_DIR}/{layout.SKILLS_DIR}/") or not path.endswith(".browser.md"):
        raise ValueError("Generated browser skills must use .proofsignal/skills/<name>.browser.md.")
    return path


def _skill_reference(value: Any) -> ArtifactReference:
    path = _skill_path(value)
    name = Path(path).stem.removesuffix(".browser")
    return ArtifactReference(path=path, kind="skill", generated=True, id=f"skill.{name}", version="1.0.0")


def _runtime_input(value: Any) -> RuntimeInputRequirement:
    if isinstance(value, dict):
        return RuntimeInputRequirement.from_dict(value)
    return RuntimeInputRequirement(name=str(value))


def _question_from_dict(data: dict[str, Any]) -> AuthoringQuestion:
    question = AuthoringQuestion.from_dict(data)
    if _is_environment_dependent(data) and question.status != "answered":
        question.status = data.get("status", "pending")
        question.affects = question.affects or str(data.get("affects") or "runtime")
    return question


def _apply_answer(questions: list[AuthoringQuestion], answer: dict[str, Any]) -> None:
    question_id = str(answer.get("questionId") or answer.get("id") or "")
    for question in questions:
        if question.id == question_id:
            question.status = "answered"
            question.answerSummary = str(answer.get("answerSummary") or answer.get("summary") or "")
            return


def _is_environment_dependent(data: dict[str, Any]) -> bool:
    text = " ".join(str(data.get(key, "")) for key in ["prompt", "reason", "affects", "category"]).lower()
    return any(area.lower() in text for area in BLOCKING_CLARIFICATION_AREAS) or bool(data.get("environmentDependent"))


def _artifact_content(value: Any) -> str | None:
    if isinstance(value, dict):
        content = value.get("content")
        return str(content) if content is not None else None
    return None


def _ensure_core_run_request_document(content: str | None, record: Any, payload: dict[str, Any]) -> str:
    if content and _looks_like_core_run_request(content):
        return content
    return artifacts.render_run_request(record, parameters=_parameters_from_payload(payload))


def _ensure_core_skill_document(content: str | None, record: Any, skill: ArtifactReference, payload: Any) -> str:
    if content and _looks_like_core_skill(content):
        return content
    return artifacts.render_skill(record, skill, draft_notes=_skill_notes_from_payload(content, payload), browser=_browser_from_payload(payload))


def _looks_like_core_run_request(content: str) -> bool:
    return all(token in content for token in ["schemaVersion: qa-run-request/v1", "request:", "id:", "name:", "target:", "validationScope:", "skills:"])


def _looks_like_core_skill(content: str) -> bool:
    return all(token in content for token in ["schemaVersion: qa-skill/v1", "skill:", "kind: browser", "browser:"])


def _parameters_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    run_request = payload.get("runRequest") if isinstance(payload.get("runRequest"), dict) else {}
    run_request_intent = run_request.get("intent") if isinstance(run_request.get("intent"), dict) else {}
    parameters = run_request.get("parameters") if isinstance(run_request, dict) else {}
    if isinstance(parameters, dict) and parameters:
        return dict(parameters)
    intent_parameters = run_request_intent.get("parameters")
    if isinstance(intent_parameters, dict) and intent_parameters:
        return dict(intent_parameters)
    runtime_inputs = payload.get("runtimeInputs")
    if not runtime_inputs and isinstance(run_request, dict):
        runtime_inputs = run_request.get("runtimeInputs") or run_request_intent.get("runtimeInputs")
    return {item["name"]: item.get("value", item.get("default", "")) for item in runtime_inputs or [] if isinstance(item, dict) and item.get("name")}


def _runtime_inputs_from_run_request_payload(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, dict):
        return []
    runtime_inputs = payload.get("runtimeInputs")
    if isinstance(runtime_inputs, list):
        return [item for item in runtime_inputs if isinstance(item, dict)]
    intent = payload.get("intent")
    if isinstance(intent, dict) and isinstance(intent.get("runtimeInputs"), list):
        return [item for item in intent["runtimeInputs"] if isinstance(item, dict)]
    content = payload.get("content")
    if not isinstance(content, str):
        return []
    try:
        import yaml  # type: ignore

        parsed = yaml.safe_load(content) or {}
    except Exception:
        return []
    runtime_inputs = parsed.get("runtimeInputs") if isinstance(parsed, dict) else None
    if isinstance(runtime_inputs, list):
        return [item for item in runtime_inputs if isinstance(item, dict)]
    parameters = parsed.get("parameters") if isinstance(parsed, dict) else None
    return _runtime_inputs_from_parameters(parameters)


def _planned_runtime_inputs(project: Path, alias: str) -> list[dict[str, Any]]:
    try:
        return load_artifact_plan(project, alias).runtimeInputs
    except Exception:
        return []


def _runtime_inputs_from_parameters(parameters: Any) -> list[dict[str, Any]]:
    if not isinstance(parameters, dict):
        return []
    return [{"name": str(name), "value": value, "source": "default", "required": True} for name, value in parameters.items()]


def _browser_from_payload(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    intent = payload.get("intent") if isinstance(payload.get("intent"), dict) else {}
    browser = payload.get("browser") if isinstance(payload.get("browser"), dict) else intent.get("browser")
    normalized = _normalize_browser_payload(browser if isinstance(browser, dict) else {})
    blockers = validate_browser_payload(normalized)
    if blockers:
        raise ValueError("Invalid executable browser skill intent: " + " ".join(blockers))
    if _has_detailed_skill_intent(payload) and not _has_executable_browser_intent(normalized, payload):
        raise ValueError(
            "Browser skill intent includes detailed validation instructions, but no executable browser.steps/assertions were provided. "
            "Provide Core browser actions under intent.browser.steps and final checks under intent.browser.assertions."
        )
    return normalized


def _skill_notes_from_payload(content: str | None, payload: Any) -> str | None:
    if content:
        return content
    if not isinstance(payload, dict):
        return None
    intent = payload.get("intent") if isinstance(payload.get("intent"), dict) else {}
    body = intent.get("body") or payload.get("body")
    if isinstance(body, str) and body.strip():
        return body
    steps = intent.get("steps") or payload.get("steps")
    if not isinstance(steps, list) or not steps:
        return None
    lines = ["## Execution Intent", ""]
    for index, step in enumerate(steps, start=1):
        if isinstance(step, dict):
            title = step.get("title") or step.get("id") or f"Step {index}"
            lines.extend([f"{index}. {title}", ""])
            instructions = step.get("instructions") or step.get("description")
            if instructions:
                lines.extend([str(instructions), ""])
            if step.get("gate"):
                lines.extend([f"Gate: {step['gate']}", ""])
        else:
            lines.extend([f"{index}. {step}", ""])
    success_gate = intent.get("successGate") or payload.get("successGate")
    if success_gate:
        lines.extend(["Success gate:", str(success_gate), ""])
    return "\n".join(lines).strip()


def _normalize_browser_payload(browser: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(browser)
    start_url = normalized.pop("startUrl", None)
    timeout_ms = normalized.pop("timeoutMs", None)
    steps = list(normalized.get("steps") or [])
    assertions = list(normalized.get("assertions") or [])
    if start_url and not steps:
        step: dict[str, Any] = {"id": "open", "action": "navigate", "value": start_url}
        if timeout_ms:
            step["timeoutMs"] = timeout_ms
        steps = [step]
    if steps or assertions or start_url:
        normalized["steps"] = steps
        normalized["assertions"] = assertions
    return normalized


def _has_detailed_skill_intent(payload: dict[str, Any]) -> bool:
    intent = payload.get("intent") if isinstance(payload.get("intent"), dict) else {}
    detailed = [
        intent.get("body"),
        intent.get("steps"),
        intent.get("successGate"),
        payload.get("body"),
        payload.get("steps"),
        payload.get("validationGates"),
    ]
    return any(bool(item) for item in detailed)


def _has_executable_browser_intent(browser: dict[str, Any], payload: dict[str, Any]) -> bool:
    steps = browser.get("steps") if isinstance(browser.get("steps"), list) else []
    assertions = browser.get("assertions") if isinstance(browser.get("assertions"), list) else []
    intent = payload.get("intent") if isinstance(payload.get("intent"), dict) else {}
    planned_steps = intent.get("steps") or payload.get("steps")
    planned_count = len(planned_steps) if isinstance(planned_steps, list) else 0
    executable_count = len(steps) + len(assertions)
    if planned_count:
        return executable_count >= planned_count and any(isinstance(step, dict) and step.get("action") for step in steps)
    return bool(assertions) or any(isinstance(step, dict) and step.get("action") and step.get("action") != "navigate" for step in steps)


def _write_payload_artifact(project: Path, rel_path: str, content: str | None, fallback) -> None:
    path = layout.project_relative_path(project, rel_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if content is None:
        content = fallback()
    path.write_text(content if content.endswith("\n") else content + "\n", encoding="utf-8")


def _artifact(project: Path, path: Path, kind: str) -> ManagedWorkspaceArtifact:
    return ManagedWorkspaceArtifact(path=project_relative(project, path), kind=kind)


def _blocked(
    stage: str,
    alias: str | None,
    *,
    code: str,
    message: str,
    invalid: bool = False,
    recovery_command: str | None = None,
) -> dict[str, Any]:
    return StagePersistenceResult(
        stage=stage,
        alias=alias,
        status="invalid" if invalid else "blocked",
        blockers=[ReadinessBlocker(code=code, message=message, recoveryCommand=recovery_command)],
    ).to_dict()


def _inventory_warnings(status: str) -> list[str]:
    if status == "partial":
        return ["Coverage inventory is partial; candidate scenarios are not exhaustive."]
    if status == "stale":
        return ["Coverage inventory is stale; refresh affected areas before relying on candidates."]
    return []


def _recommended_follow_up_scope(status: str, current_scope: str) -> str | None:
    if status == "partial":
        return "continue"
    if status == "stale":
        return "changed" if current_scope != "all" else "all"
    return None
