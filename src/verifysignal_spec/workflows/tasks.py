from __future__ import annotations

from pathlib import Path

from verifysignal_spec.workspace import layout

from .models import ArtifactPlan, AuthoringTask, AuthoringTaskSet
from .repository import fingerprint_text


def generate_authoring_tasks(project: Path, plan: ArtifactPlan) -> AuthoringTaskSet:
    source = layout.workflow_stage_document_path(project, plan.useCaseAlias, "plan")
    source_text = source.read_text(encoding="utf-8") if source.exists() else plan.to_dict().__repr__()
    entries = [
        AuthoringTask("A001", "Update use case metadata and workflow reference.", f".verifysignal/use-cases/{plan.useCaseAlias}.yaml"),
        AuthoringTask("A002", "Draft the planned run request.", plan.runRequest),
        AuthoringTask("A003", "Draft or reuse the planned main skill.", plan.mainSkill),
    ]
    for index, skill in enumerate(plan.supportingSkills, start=4):
        entries.append(AuthoringTask(f"A{index:03d}", "Draft or reuse supporting skill.", skill))
    entries.append(AuthoringTask(f"A{len(entries) + 1:03d}", "Run VerifySignal validation before marking runnable.", "verifysignal validate"))
    return AuthoringTaskSet(
        taskSetId=f"tasks-{plan.useCaseAlias}",
        useCaseAlias=plan.useCaseAlias,
        sourcePlanPath=source.as_posix(),
        planFingerprint=fingerprint_text(source_text),
        generatedAt="",
        tasks=entries,
    )
