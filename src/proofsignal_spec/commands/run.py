from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from proofsignal_spec.core.adapter import CoreAdapter, core_status
from proofsignal_spec.workspace.models import RunHistoryEntry
from proofsignal_spec.workspace.repository import get_core_command, now_iso, record_run, resolve_artifacts


def run(project: Path, alias: str, profile_name: str = "normal", interactive: bool = True, core_cmd: str | None = None) -> dict[str, Any]:
    record, run_request, main_skill, skills = resolve_artifacts(project, alias)
    profile = next((item for item in record.profiles if item.name == profile_name), None)
    if profile is None:
        raise ValueError(f"Unknown profile for {alias}: {profile_name}")
    runtime_values = resolve_runtime_inputs(record.runtimeInputs, interactive=interactive)
    output_dir = project / ".proofsignal" / "runs" / alias
    result = CoreAdapter(executable=core_cmd or get_core_command(project), cwd=project).run(
        run_request,
        main_skill,
        skills,
        output_dir=output_dir,
        headed=profile.headed,
        slow_mo_ms=profile.slowMoMs,
        env=runtime_values,
    )
    data = result.get("data", {})
    run_id = data.get("runId") or f"{alias}-{now_iso().replace(':', '').replace('-', '')}"
    entry = RunHistoryEntry(
        runId=run_id,
        useCaseAlias=alias,
        profile=profile_name,
        status=core_status(result),
        startedAt=now_iso(),
        completedAt=now_iso(),
        summary=data.get("summary") or result.get("summary"),
        reportPath=data.get("reportPath"),
        evidenceDir=data.get("evidencePath") or data.get("evidenceDir"),
    )
    record_run(project, entry)
    return {"alias": alias, "status": entry.status, "reportPath": entry.reportPath, "evidenceDir": entry.evidenceDir, "core": result}
