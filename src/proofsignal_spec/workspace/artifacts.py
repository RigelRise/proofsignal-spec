from __future__ import annotations

from pathlib import Path
from typing import Any

from . import layout
from .models import ArtifactReference, UseCaseRecord


def render_run_request(
    record: UseCaseRecord,
    parameters: dict[str, Any] | None = None,
    *,
    schema_version: str = "qa-run-request/v1",
) -> str:
    skill_refs = [{"id": skill.id or f"skill.{record.alias}", "version": skill.version or "1.0.0"} for skill in record.skills]
    import json

    resolved_parameters = dict(parameters or {})
    for item in record.runtimeInputs:
        if item.kind == "credential":
            continue
        resolved_parameters.setdefault(item.name, "")
    document: dict[str, Any] = {
        "schemaVersion": schema_version,
        "request": {"id": f"request.{record.alias}", "name": record.title},
        "target": "browser",
        "validationScope": "feature-level",
        "skills": skill_refs,
        "parameters": resolved_parameters,
    }
    if record.credentialRefs:
        document["credentialRefs"] = record.credentialRefs
    return json.dumps(document, indent=2) + "\n"


def render_skill(
    record: UseCaseRecord,
    skill: ArtifactReference | None = None,
    *,
    draft_notes: str | None = None,
    browser: dict[str, Any] | None = None,
    schema_version: str = "qa-skill/v1",
) -> str:
    skill = skill or record.mainSkill
    skill_id = skill.id if skill and skill.id else f"skill.{record.alias}"
    skill_name = _skill_name(skill_id, record.title)
    browser_yaml = _render_browser_section(browser or {}, record)
    parameters_yaml = _render_skill_parameters(record)
    notes = f"\n## Draft Instructions\n\n{draft_notes.strip()}\n" if draft_notes else ""
    return f"""# {skill_name}

```yaml
schemaVersion: {schema_version}
skill:
  id: {skill_id}
  version: 1.0.0
  kind: browser
  name: {skill_name}
  description: {record.description}
  status: draft
parameters:
{parameters_yaml}
failurePolicy:
  stopOnFailure: true
  retries: 0
evidence:
  required: [report, run-log, failure-screenshot]
  optional: [screenshot, video, network]
browser:
{browser_yaml}
```

## Purpose

{record.description}

Keep credential values in runtime inputs or environment variables. Do not
persist secrets in this skill.
{notes}
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
                skill_path.write_text(render_skill(record, skill), encoding="utf-8")


def link_external_artifact(path: str, kind: str, artifact_id: str | None = None, version: str | None = None) -> ArtifactReference:
    if kind not in {"run-request", "skill", "external"}:
        raise ValueError(f"Unsupported artifact kind: {kind}")
    return ArtifactReference(path=path, kind=kind, generated=False, id=artifact_id, version=version)


def _skill_name(skill_id: str, fallback: str) -> str:
    name = skill_id.removeprefix("skill.").replace("-", " ").replace("_", " ").strip()
    return name.title() if name else fallback


def _render_skill_parameters(record: UseCaseRecord) -> str:
    if not record.runtimeInputs:
        return "  []"
    lines: list[str] = []
    for item in record.runtimeInputs:
        if item.kind == "credential":
            continue
        lines.extend(
            [
                f"  - name: {item.name}",
                "    type: string",
                f"    required: {str(item.required).lower()}",
            ]
        )
    return "\n".join(lines)


def _render_browser_section(browser: dict[str, Any], record: UseCaseRecord) -> str:
    if browser:
        try:
            import yaml  # type: ignore

            rendered = yaml.safe_dump(browser, sort_keys=False).rstrip()
        except Exception:
            import json

            rendered = json.dumps(browser, indent=2)
        return "\n".join(f"  {line}" for line in rendered.splitlines())
    start = "{{parameters.baseUrl}}" if any(item.name == "baseUrl" for item in record.runtimeInputs) else "about:blank"
    return "\n".join(
        [
            "  targets: {}",
            "  steps:",
            "    - id: open",
            "      action: navigate",
            f"      value: \"{start}\"",
            "      timeoutMs: 30000",
            "  assertions: []",
        ]
    )
