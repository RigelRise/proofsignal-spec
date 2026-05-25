from __future__ import annotations

from pathlib import Path

from . import layout
from .models import ArtifactReference, UseCaseRecord


def render_run_request(record: UseCaseRecord) -> str:
    skill_refs = [{"id": skill.id or f"skill.{record.alias}", "version": skill.version or "1.0.0"} for skill in record.skills]
    import json

    return json.dumps(
        {
            "schemaVersion": "qa-run-request/v1",
            "request": {"id": f"request.{record.alias}", "name": record.title},
            "target": "browser",
            "validationScope": "feature-level",
            "skills": skill_refs,
        },
        indent=2,
    ) + "\n"


def render_skill(record: UseCaseRecord) -> str:
    return f"""---
schemaVersion: qa-skill/v1
skill:
  id: skill.{record.alias}
  version: 1.0.0
  kind: browser
  name: {record.title}
  description: {record.description}
---

# {record.title}

Validate this browser behavior:

{record.description}

Keep credential values in runtime inputs or environment variables. Do not
persist secrets in this skill.
"""


def write_generated_artifacts(project: Path, record: UseCaseRecord, overwrite: bool = False) -> None:
    if record.runRequest and record.runRequest.generated:
        run_path = layout.project_relative_path(project, record.runRequest.path)
        if overwrite or not run_path.exists():
            run_path.parent.mkdir(parents=True, exist_ok=True)
            run_path.write_text(render_run_request(record), encoding="utf-8")
    for skill in record.skills:
        if skill.generated:
            skill_path = layout.project_relative_path(project, skill.path)
            if overwrite or not skill_path.exists():
                skill_path.parent.mkdir(parents=True, exist_ok=True)
                skill_path.write_text(render_skill(record), encoding="utf-8")


def link_external_artifact(path: str, kind: str, artifact_id: str | None = None, version: str | None = None) -> ArtifactReference:
    if kind not in {"run-request", "skill", "external"}:
        raise ValueError(f"Unsupported artifact kind: {kind}")
    return ArtifactReference(path=path, kind=kind, generated=False, id=artifact_id, version=version)
