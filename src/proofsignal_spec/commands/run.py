from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from proofsignal_spec.core.adapter import CoreAdapter, core_status
from proofsignal_spec.workflows.authoring_coherence import evaluate_persisted_coherence
from proofsignal_spec.workflows.evidence import normalize_planned_gates
from proofsignal_spec.workflows.gate_coverage import coverage_status
from proofsignal_spec.workflows.repair_recommendations import recommend_repairs_for_gate_coverage
from proofsignal_spec.workflows.repository import load_artifact_plan
from proofsignal_spec.workspace.models import RunHistoryEntry
from proofsignal_spec.workspace.repository import get_core_command, load_document, load_use_case, now_iso, record_run, resolve_artifacts


def run(project: Path, alias: str, profile_name: str = "normal", interactive: bool = True, core_cmd: str | None = None) -> dict[str, Any]:
    record = load_use_case(project, alias)
    profile = next((item for item in record.profiles if item.name == profile_name), None)
    if profile is None:
        available = ", ".join(item.name for item in record.profiles) or "normal"
        raise ValueError(f"Unknown profile for {alias}: {profile_name}. Available profiles: {available}.")
    record, run_request, main_skill, skills = resolve_artifacts(project, alias)
    runtime_values = resolve_runtime_inputs(
        record.runtimeInputs,
        interactive=interactive,
        provided=_run_request_parameters(run_request),
    )
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
    core = core_status(result)
    coherence = evaluate_persisted_coherence(project, alias)
    gate_coverage = [item.to_dict() for item in coherence.gateCoverage]
    try:
        gates, _warnings = normalize_planned_gates(load_artifact_plan(project, alias).validationGates)
    except Exception:
        gates = []
    contradictions = [
        item.to_dict()
        for item in recommend_repairs_for_gate_coverage(coherence.gateCoverage, gates, source_run_id=str(run_id))
    ]
    spec_status = coverage_status(core, coherence.gateCoverage)
    profile_settings = {"headed": profile.headed, "slowMoMs": profile.slowMoMs}
    entry = RunHistoryEntry(
        runId=run_id,
        useCaseAlias=alias,
        profile=profile_name,
        status=core,
        coreStatus=core,
        coverageStatus=spec_status,
        profileSettings=profile_settings,
        gateCoverage=gate_coverage,
        runtimeContradictions=contradictions,
        startedAt=now_iso(),
        completedAt=now_iso(),
        summary={
            "core": data.get("summary") or result.get("summary"),
            "coverageStatus": spec_status,
            "mainSkill": record.mainSkill.path if record.mainSkill else str(main_skill),
        },
        reportPath=data.get("reportPath"),
        evidenceDir=data.get("evidencePath") or data.get("evidenceDir"),
    )
    record_run(project, entry)
    return {
        "alias": alias,
        "status": entry.status,
        "coreStatus": core,
        "coverageStatus": spec_status,
        "selectedMainSkill": record.mainSkill.path if record.mainSkill else str(main_skill),
        "profile": profile_name,
        "profileSettings": profile_settings,
        "gateCoverage": gate_coverage,
        "runtimeContradictions": contradictions,
        "reportPath": entry.reportPath,
        "evidenceDir": entry.evidenceDir,
        "core": result,
    }


def _run_request_parameters(run_request: Path) -> dict[str, Any]:
    data = load_document(run_request, default={}) or {}
    if not isinstance(data, dict):
        return {}
    parameters = data.get("parameters")
    if isinstance(parameters, dict):
        return dict(parameters)
    runtime_inputs = data.get("runtimeInputs")
    if isinstance(runtime_inputs, list):
        return {
            str(item["name"]): value
            for item in runtime_inputs
            if isinstance(item, dict)
            and item.get("name")
            for value in [item.get("value", item.get("default"))]
            if value is not None and value != ""
        }
    return {}
