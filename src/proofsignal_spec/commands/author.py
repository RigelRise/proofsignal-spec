from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace import artifacts, layout
from proofsignal_spec.workspace.models import ArtifactReference, AuthoringQuestion
from proofsignal_spec.workspace.product_context import append_validation_goal
from proofsignal_spec.workspace.repository import create_default_use_case, save_use_case
from proofsignal_spec.workflows.first_run import advance_guided_first_run_state


def run(project: Path, alias: str, description: str, run_request: str | None = None, skills: list[str] | None = None) -> dict[str, Any]:
    layout.ensure_path_safe_alias(alias)
    record = create_default_use_case(project, alias, description)
    record.authoringQuestions = [
        AuthoringQuestion(
            id="q1",
            prompt="What local URL or baseUrl should this browser use case start from?",
            reason="Browser validation needs an explicit target URL or runtime input.",
            status="deferred",
            affects="runtimeInputs.baseUrl",
        )
    ]
    if run_request:
        record.runRequest = artifacts.link_external_artifact(run_request, "run-request")
    if skills:
        record.skills = [artifacts.link_external_artifact(path, "skill") for path in skills]
        record.mainSkill = record.skills[0] if record.skills else record.mainSkill
    else:
        artifacts.write_generated_artifacts(project, record)
    save_use_case(project, record)
    append_validation_goal(project, description)
    owned_artifacts = []
    if record.runRequest:
        owned_artifacts.append(record.runRequest.path)
    owned_artifacts.extend(skill.path for skill in record.skills)
    guided_state = advance_guided_first_run_state(
        project,
        alias,
        stage="validating",
        first_run_status="not-started",
        resume_command=f"proofsignal-spec validate {alias} --runtime-readiness --json",
        summary=f"{alias} artifacts are authored and ready for validation.",
        owned_artifacts=owned_artifacts,
    )
    return {
        "alias": record.alias,
        "status": record.status,
        "recordPath": f".proofsignal/use-cases/{record.alias}.yaml",
        "runRequest": record.runRequest.to_dict() if record.runRequest else None,
        "skills": [skill.to_dict() for skill in record.skills],
        "questions": [question.to_dict() for question in record.authoringQuestions],
        "guidedFirstRunState": guided_state or None,
    }
