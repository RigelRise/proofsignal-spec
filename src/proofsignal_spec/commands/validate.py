from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.workspace.repository import get_core_command, resolve_artifacts, update_validation


def run(project: Path, alias: str, runtime_readiness: bool = False, core_cmd: str | None = None) -> dict[str, Any]:
    record, run_request, main_skill, skills = resolve_artifacts(project, alias)
    result = CoreAdapter(executable=core_cmd or get_core_command(project), cwd=project).authoring_check(run_request, main_skill, skills, runtime_readiness=runtime_readiness)
    update_validation(project, alias, result)
    return {"alias": alias, "status": result.get("status", "error"), "core": result}
