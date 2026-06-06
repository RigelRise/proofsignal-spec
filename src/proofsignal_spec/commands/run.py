from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from proofsignal_spec.commands.runtime_inputs import resolve_runtime_inputs
from proofsignal_spec.core.adapter import CoreAdapter, core_status
from proofsignal_spec.core.errors import CoreMissingError
from proofsignal_spec.runtime.entitlement import load_receipt, receipt_status
from proofsignal_spec.runtime.resolver import ensure_core_runtime
from proofsignal_spec.workflows.browser_authoring import resolve_effective_profile_settings
from proofsignal_spec.workflows.evidence import extract_core_runtime_evidence, normalize_planned_gates
from proofsignal_spec.workflows.first_run import classify_first_run_status, golden_path_state, update_golden_path_run_state
from proofsignal_spec.workflows.gate_coverage import calculate_gate_coverage, coverage_status
from proofsignal_spec.workflows.models import GateCoverageResult, GoldenPathRunState, RepairRecommendation, RunOutcomeSummary
from proofsignal_spec.workflows.repair_recommendations import recommend_repairs_for_gate_coverage
from proofsignal_spec.workflows.readiness import executable_contract_blockers, legacy_executable_artifact_blockers, managed_runtime_contract_blockers
from proofsignal_spec.workflows.stage_cards import run_result_card
from proofsignal_spec.workflows.repository import load_artifact_plan
from proofsignal_spec.workspace.models import ArtifactReference, RunHistoryEntry
from proofsignal_spec.workspace.repository import load_document, load_use_case, now_iso, record_run, resolve_artifacts


def run(
    project: Path,
    alias: str,
    profile_name: str = "normal",
    interactive: bool = True,
    core_cmd: str | None = None,
    api_base_url: str | None = None,
    slow_mo_override: int | None = None,
) -> dict[str, Any]:
    record = load_use_case(project, alias)
    profile = next((item for item in record.profiles if item.name == profile_name), None)
    if profile is None:
        available = ", ".join(item.name for item in record.profiles) or "normal"
        raise ValueError(f"Unknown profile for {alias}: {profile_name}. Available profiles: {available}.")
    record, run_request, main_skill, skills = resolve_artifacts(project, alias)
    managed_runtime = ensure_core_runtime(project, explicit_core_cmd=core_cmd, api_base_url=api_base_url, context="run")
    if managed_runtime.status != "ready":
        contract_blockers = managed_runtime_contract_blockers(managed_runtime)
        if contract_blockers:
            return {
                "alias": alias,
                "status": "blocked",
                "coreStatus": "blocked",
                "coverageStatus": "not-run",
                "coreBrowserStatus": "blocked",
                "specCoverageStatus": "not-run",
                "managedRuntimeReadiness": managed_runtime.to_dict(),
                "blockers": [blocker.to_dict() for blocker in contract_blockers],
                "reason": contract_blockers[0].message,
                "nextAction": f"proofsignal workflow check run --alias {alias} --json",
            }
        if any(blocker.code == "core.missing" for blocker in managed_runtime.blockers):
            raise CoreMissingError(f"{managed_runtime.message} proofsignal core setup --json")
        return {
            "alias": alias,
            "status": "blocked",
            "coreStatus": "blocked",
            "coverageStatus": "not-run",
            "coreBrowserStatus": "blocked",
            "specCoverageStatus": "not-run",
            "managedRuntimeReadiness": managed_runtime.to_dict(),
            "blockers": [blocker.to_dict() for blocker in managed_runtime.blockers],
            "reason": managed_runtime.message,
            "nextAction": managed_runtime.nextAction,
        }
    profile_settings_model = resolve_effective_profile_settings(profile, slow_mo_override=slow_mo_override)
    contract_blockers = [
        *legacy_executable_artifact_blockers(run_request, main_skill, skills),
        *executable_contract_blockers(project, managed_runtime.runtimeCommand),
    ]
    if contract_blockers:
        return {
            "alias": alias,
            "status": "blocked",
            "coreStatus": "blocked",
            "coverageStatus": "not-run",
            "coreBrowserStatus": "blocked",
            "specCoverageStatus": "not-run",
            "selectedMainSkill": _selected_main_skill(record.mainSkill, main_skill),
            "profile": profile_name,
            "profileSettings": profile_settings_model.to_dict(),
            "managedRuntimeReadiness": managed_runtime.to_dict(),
            "blockers": [blocker.to_dict() for blocker in contract_blockers],
            "reason": contract_blockers[0].message,
            "nextAction": f"proofsignal workflow check run --alias {alias} --json",
        }
    runtime_values = resolve_runtime_inputs(
        record.runtimeInputs,
        interactive=interactive,
        provided=_run_request_parameters(run_request),
    )
    output_dir = project / ".proofsignal" / "runs" / alias
    result = CoreAdapter(executable=managed_runtime.runtimeCommand, cwd=project).run(
        run_request,
        main_skill,
        skills,
        output_dir=output_dir,
        headed=profile_settings_model.headed,
        slow_mo_ms=profile_settings_model.slowMoMs,
        env=runtime_values,
        entitlement_receipt=_valid_receipt_path(),
    )
    data = result.get("data", {})
    run_id = data.get("runId") or f"{alias}-{now_iso().replace(':', '').replace('-', '')}"
    core = core_status(result)
    gates = _planned_gates(project, alias)
    gate_coverage_results = _runtime_gate_coverage(project, result, gates)
    gate_coverage = [item.to_dict() for item in gate_coverage_results]
    contradictions = (
        [
            item.to_dict()
            for item in recommend_repairs_for_gate_coverage(gate_coverage_results, gates, source_run_id=str(run_id))
        ]
        if core not in {"failed", "error", "blocked"}
        else []
    )
    repair_recommendations = [
        item.to_dict()
        for item in _repair_recommendations_from_gate_coverage(gate_coverage_results, core, source_run_id=str(run_id))
    ]
    spec_coverage_status = coverage_status(core, gate_coverage_results)
    selected_main_skill = _selected_main_skill(record.mainSkill, main_skill)
    executed_skill = _executed_skill(data)
    skill_selection_status = _skill_selection_status(selected_main_skill, executed_skill)
    missing_required_gates = _missing_required_gates(gate_coverage_results)
    use_case_status = _use_case_status(core, spec_coverage_status)
    profile_settings = profile_settings_model.to_dict()
    if not profile_settings.get("overrides"):
        profile_settings.pop("overrides", None)
    partial_coverage = gate_coverage if core in {"failed", "error", "blocked"} else []
    reason = _reason(use_case_status, core, missing_required_gates, skill_selection_status)
    next_action = _next_action(use_case_status, alias)
    failed_step = _failed_step(result)
    outcome_summary = RunOutcomeSummary(
        alias=alias,
        overallStatus=use_case_status,
        coreBrowserStatus=core,
        specCoverageStatus=spec_coverage_status,
        selectedMainSkill=selected_main_skill,
        profile=profile_name,
        runId=str(run_id),
        failedStep=failed_step,
        nextAction=next_action,
    ).to_dict()
    first_run_payload = _first_run_payload(
        project,
        alias,
        core,
        spec_coverage_status,
        missing_required_gates,
        next_action,
        _run_request_parameters(run_request).get("baseUrl", ""),
    )
    if first_run_payload:
        outcome_summary.update(
            {
                "firstRunStatus": first_run_payload["firstRunStatus"],
                "strictPass": first_run_payload["strictPass"],
                "stageCards": first_run_payload["stageCards"],
            }
        )
    entry = RunHistoryEntry(
        runId=run_id,
        useCaseAlias=alias,
        profile=profile_name,
        status=use_case_status,
        coreStatus=core,
        coverageStatus=spec_coverage_status,
        profileSettings=profile_settings,
        selectedMainSkill=selected_main_skill,
        executedSkill=executed_skill,
        skillSelectionStatus=skill_selection_status,
        gateCoverage=gate_coverage,
        missingRequiredGates=missing_required_gates,
        partialCoverage=partial_coverage,
        runtimeContradictions=contradictions,
        repairRecommendations=repair_recommendations,
        startedAt=now_iso(),
        completedAt=now_iso(),
        summary={
            "core": data.get("summary") or result.get("summary"),
            "status": use_case_status,
            "coverageStatus": spec_coverage_status,
            "coreBrowserStatus": core,
            "specCoverageStatus": spec_coverage_status,
            "reason": reason,
            "nextAction": next_action,
            "mainSkill": selected_main_skill,
            "runOutcomeSummary": outcome_summary,
        },
        reportPath=data.get("reportPath"),
        evidenceDir=data.get("evidencePath") or data.get("evidenceDir"),
    )
    record_run(project, entry)
    return {
        "alias": alias,
        "status": entry.status,
        "coreStatus": core,
        "coverageStatus": spec_coverage_status,
        "coreBrowserStatus": core,
        "specCoverageStatus": spec_coverage_status,
        "runOutcomeSummary": outcome_summary,
        **first_run_payload,
        "selectedMainSkill": selected_main_skill,
        "executedSkill": executed_skill,
        "skillSelectionStatus": skill_selection_status,
        "profile": profile_name,
        "profileSettings": profile_settings,
        "managedRuntimeReadiness": managed_runtime.to_dict(),
        "gateCoverage": gate_coverage,
        "missingRequiredGates": missing_required_gates,
        "partialCoverage": partial_coverage,
        "runtimeContradictions": contradictions,
        "repairRecommendations": repair_recommendations,
        "reason": reason,
        "nextAction": next_action,
        "reportPath": entry.reportPath,
        "evidenceDir": entry.evidenceDir,
        "core": result,
    }


def _first_run_payload(
    project: Path,
    alias: str,
    core_browser_status: str,
    spec_coverage_status: str,
    missing_required_gates: list[str],
    next_action: str,
    target: str,
) -> dict[str, Any]:
    state = golden_path_state(project)
    if state.get("selectedCandidate") != alias or state.get("recommendationStatus") != "accepted":
        return {}
    repaired = bool(state.get("repairFeedback"))
    first_run_status, strict_pass = classify_first_run_status(
        core_browser_status,
        spec_coverage_status,
        missing_required_gates,
        repaired=repaired,
    )
    stage_cards = [
        run_result_card(
            alias=alias,
            first_run_status=first_run_status,
            strict_pass=strict_pass,
            core_browser_status=core_browser_status,
            spec_coverage_status=spec_coverage_status,
            missing_required_gates=missing_required_gates,
            next_action=next_action,
        )
    ]
    run_state = GoldenPathRunState.from_run_result(
        use_case_alias=alias,
        target=str(target or ""),
        core_browser_status=core_browser_status,
        spec_coverage_status=spec_coverage_status,
        missing_required_gates=missing_required_gates,
        repaired=repaired,
        repair_feedback=list(state.get("repairFeedback", [])),
        stage_cards=stage_cards,
    )
    update_golden_path_run_state(project, run_state)
    return {
        "firstRunStatus": first_run_status,
        "strictPass": strict_pass,
        "stageCards": stage_cards,
    }


def _planned_gates(project: Path, alias: str) -> list[Any]:
    try:
        gates, _warnings = normalize_planned_gates(load_artifact_plan(project, alias).validationGates)
        return gates
    except Exception:
        return []


def _runtime_gate_coverage(project: Path, result: dict[str, Any], gates: list[Any]) -> list[GateCoverageResult]:
    if not gates:
        return []
    evidence = extract_core_runtime_evidence(
        _result_with_public_report(project, result),
        known_gate_ids={gate.id for gate in gates},
    )
    return calculate_gate_coverage(gates, evidence)


def _result_with_public_report(project: Path, result: dict[str, Any]) -> dict[str, Any]:
    data = result.get("data") if isinstance(result.get("data"), dict) else {}
    if isinstance(data.get("report"), dict):
        return result
    report = _load_public_qa_report(project, data.get("reportPath"))
    if report is None:
        return result
    updated = dict(result)
    updated_data = dict(data)
    updated_data["report"] = report
    updated["data"] = updated_data
    return updated


def _load_public_qa_report(project: Path, raw_path: Any) -> dict[str, Any] | None:
    report_path = _resolve_report_path(project, raw_path)
    if report_path is None or not report_path.exists():
        return None
    try:
        data = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict) or data.get("schemaVersion") != "qa-report/v1":
        return None
    return data


def _resolve_report_path(project: Path, raw_path: Any) -> Path | None:
    if not raw_path:
        return None
    path = Path(str(raw_path))
    candidate = path if path.is_absolute() else project / path
    try:
        resolved = candidate.resolve()
        workspace = (project / ".proofsignal").resolve()
    except Exception:
        return None
    if resolved == workspace or workspace in resolved.parents:
        return resolved
    return None


def _selected_main_skill(reference: ArtifactReference | None, path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {"path": str(reference.path if reference else path)}
    if reference and reference.id:
        data["id"] = reference.id
    if reference and reference.version:
        data["version"] = reference.version
    return data


def _executed_skill(data: dict[str, Any]) -> dict[str, Any] | None:
    raw = data.get("executedSkill") or data.get("executedSkillId")
    if not raw:
        return None
    if isinstance(raw, dict):
        result = dict(raw)
        result.setdefault("source", "core-public-result")
        return result
    return {"id": str(raw), "source": "core-public-result"}


def _skill_selection_status(selected: dict[str, Any], executed: dict[str, Any] | None) -> str:
    if not executed:
        return "unknown"
    selected_tokens = {str(value) for value in [selected.get("id"), selected.get("path")] if value}
    selected_tokens.update(Path(token).name for token in list(selected_tokens))
    executed_tokens = {str(value) for value in [executed.get("id"), executed.get("path")] if value}
    executed_tokens.update(Path(token).name for token in list(executed_tokens))
    return "matched" if selected_tokens & executed_tokens else "mismatch"


def _missing_required_gates(gate_coverage: list[GateCoverageResult]) -> list[str]:
    incomplete = {"missing", "network-only", "screenshot-only", "unmapped", "not-evaluated", "incomplete"}
    return [item.gateId for item in gate_coverage if item.required and item.status in incomplete]


def _use_case_status(core: str, spec_coverage_status: str) -> str:
    if core in {"failed", "error", "blocked"}:
        return "failed"
    if spec_coverage_status != "complete":
        return "incomplete"
    return "passed"


def _reason(status: str, core: str, missing_required_gates: list[str], skill_selection_status: str) -> str:
    if status == "passed":
        return "Core passed and all planned required validation gates were evidenced."
    if status == "failed":
        return f"Core/browser execution reported {core}; Spec coverage is diagnostic only because runtime evidence may not have been committed."
    pieces = ["Core passed but required validation gates are missing or incomplete."]
    if missing_required_gates:
        pieces.append(f"Missing required gates: {', '.join(missing_required_gates)}.")
    if skill_selection_status == "mismatch":
        pieces.append("Core executed a different skill than the planned main validation skill.")
    return " ".join(pieces)


def _next_action(status: str, alias: str) -> str:
    if status == "passed":
        return "No repair needed."
    if status == "incomplete":
        return f"Run `proofsignal repair {alias} --json` or re-run after repairing missing gate evidence."
    return f"Inspect the Core report and run `proofsignal repair {alias} --from-report <report> --json`."


def _failed_step(result: dict[str, Any]) -> str | None:
    data = result.get("data", {}) if isinstance(result.get("data"), dict) else {}
    summary = data.get("summary") if isinstance(data.get("summary"), dict) else {}
    return data.get("failedStep") or data.get("failedStepId") or summary.get("failedStepId")


def _repair_recommendations_from_gate_coverage(
    gate_coverage: list[GateCoverageResult],
    core: str,
    *,
    source_run_id: str,
) -> list[RepairRecommendation]:
    if core in {"failed", "error", "blocked"}:
        return []
    recommendations: list[RepairRecommendation] = []
    for item in gate_coverage:
        if not item.required or item.status not in {"missing", "network-only", "screenshot-only", "unmapped", "not-evaluated", "incomplete"}:
            continue
        recommendations.append(
            RepairRecommendation(
                id=f"repair-{item.gateId}",
                category="safe-artifact-repair",
                safeCategory="gateid-mapping",
                summary=f"Required gate {item.gateId} was not proven by runtime evidence.",
                action="Ask for confirmation before changing coverage mapping, then map specific rendered-result evidence or replan if confirmed.",
                affectedArtifacts=[],
                blockedReason="Coverage mapping changes can alter validation intent and require confirmation.",
                requiresUserDecision=True,
                sourceFeedback=[source_run_id, item.gateId],
            )
        )
    return recommendations


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


def _valid_receipt_path() -> str | None:
    receipt = load_receipt()
    if not receipt:
        return None
    status = receipt_status(receipt)
    return status.receiptPath if status.status == "valid" else None
