from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.repository import save_document
from proofsignal_spec.workspace.validation import validate_no_secret_values

from .models import ArtifactPlan, AuthoringTaskSet
from .repository import project_relative


def _reject_secret_text(title: str, content: str) -> None:
    findings = validate_no_secret_values({"title": title, "content": content})
    if findings:
        first = findings[0]
        raise ValueError(f"Secret-looking value in stage document at {first.get('path')}")


def write_markdown(path: Path, title: str, sections: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for heading, value in sections.items():
        lines.extend([f"## {heading}", ""])
        if isinstance(value, list):
            if not value:
                lines.append("- None recorded")
            else:
                for item in value:
                    lines.append(f"- {item}")
        elif isinstance(value, dict):
            if not value:
                lines.append("- None recorded")
            else:
                for key, item in value.items():
                    lines.append(f"- **{key}**: {item}")
        else:
            lines.append(str(value or "Not recorded."))
        lines.append("")
    content = "\n".join(lines).rstrip() + "\n"
    _reject_secret_text(title, content)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return content


def write_global_understanding(project: Path, context: dict[str, Any]) -> str:
    metadata = context.get("understanding", {})
    return write_markdown(
        layout.workflow_global_understanding_path(project),
        "ProofSignal Repository Understanding",
        {
            "Metadata": _render_understanding_metadata(metadata),
            "Project Overview": context.get("productSummary") or context.get("repositorySummary") or "",
            "Safe Inspection Paths": context.get("safeInspectionPaths", []),
            "Blocked Sensitive Paths": context.get("blockedSensitivePaths", []),
            "Candidate Validation Use Cases": _render_candidate_use_cases(context.get("candidateUseCases", [])),
            "Startup Notes": context.get("startupNotes") or context.get("localStartInstructions") or "",
            "Validation Boundaries": context.get("validationBoundaries", []),
            "Runtime Requirements": context.get("runtimeRequirements") or context.get("knownRuntimeRequirements", []),
            "Unresolved Questions": context.get("unresolvedQuestions", []),
        },
    )


def write_understanding_snapshot(project: Path, alias: str, context: dict[str, Any]) -> str:
    metadata = context.get("understanding", {})
    return write_markdown(
        layout.workflow_stage_document_path(project, alias, "understand"),
        f"Understanding Snapshot: {alias}",
        {
            "Metadata": _render_understanding_metadata(metadata),
            "Product Context": context.get("productSummary") or context.get("repositorySummary") or "",
            "Use Case Focus": context.get("useCaseFocus", alias),
            "Safe Inspection Paths": context.get("safeInspectionPaths", []),
            "Blocked Sensitive Paths": context.get("blockedSensitivePaths", []),
            "Candidate Validation Use Cases": _render_candidate_use_cases(context.get("candidateUseCases", [])),
            "Runtime Requirements": context.get("runtimeRequirements") or context.get("knownRuntimeRequirements", []),
            "Unresolved Questions": context.get("unresolvedQuestions", []),
        },
    )


def write_specification(project: Path, alias: str, goal: str, runtime_assumptions: list[str] | None = None) -> str:
    return write_markdown(
        layout.workflow_stage_document_path(project, alias, "specify"),
        f"Use Case Specification: {alias}",
        {
            "Alias": alias,
            "Purpose": goal,
            "Target Surface": "browser",
            "Expected Outcome": "To be confirmed through clarification.",
            "Runtime Assumptions": runtime_assumptions or [],
            "Acceptance Scenarios": ["To be refined before artifact planning."],
            "Unresolved Questions": ["Confirm target URL, credential group names, and expected success evidence."],
            "Public Stage Contract": _stage_contract_note("specify"),
        },
    )


def write_clarifications(project: Path, alias: str, questions: list[dict[str, Any]]) -> str:
    rendered = [f"{item.get('prompt')} ({item.get('status', 'pending')})" for item in questions]
    return write_markdown(
        layout.workflow_stage_document_path(project, alias, "clarify"),
        f"Clarifications: {alias}",
        {"Questions": rendered, "Public Stage Contract": _stage_contract_note("clarify")},
    )


def write_artifact_plan(project: Path, plan: ArtifactPlan) -> str:
    skills = [plan.mainSkill, *plan.supportingSkills]
    return write_markdown(
        layout.workflow_stage_document_path(project, plan.useCaseAlias, "plan"),
        f"Artifact Plan: {plan.useCaseAlias}",
        {
            "Run Request": plan.runRequest,
            "Reusable Skills": skills,
            "Source-Only Skills": plan.sourceOnlySkills,
            "Skill Composition": _render_skill_composition(plan.skillComposition),
            "Gate Evidence Mappings": _render_gate_evidence_mappings(plan.gateEvidenceMappings),
            "Skill Reuse": [str(item) for item in plan.skillReuse],
            "Runtime Inputs": _render_runtime_inputs(plan.runtimeInputs),
            "Preconditions": plan.preconditions,
            "Validation Gates": plan.validationGates,
            "Gate Intent Changes": plan.gateIntentChanges,
            "Public Stage Contract": _stage_contract_note("plan"),
        },
    )


def write_task_set(project: Path, task_set: AuthoringTaskSet) -> str:
    return write_markdown(
        layout.workflow_stage_document_path(project, task_set.useCaseAlias, "tasks"),
        f"Authoring Tasks: {task_set.useCaseAlias}",
        {
            "Tasks": [f"[{item.status}] {item.id}: {item.description}" for item in task_set.tasks],
            "Public Stage Contract": _stage_contract_note("tasks"),
        },
    )


def write_handoff(project: Path, alias: str, stage: str, summary: str) -> str:
    return write_markdown(
        layout.workflow_stage_document_path(project, alias, stage),
        f"Workflow Handoff: {alias}",
        {
            "Summary": summary,
            "Workflow Directory": project_relative(project, layout.workflow_use_case_dir(project, alias)),
            "Public Stage Contract": _stage_contract_note(stage) if stage in {"specify", "clarify", "plan", "tasks", "implement"} else "Not applicable.",
        },
    )


def write_validation_summary(project: Path, alias: str, result: dict[str, Any], stage: str = "validate") -> str:
    coherence = result.get("authoringCoherence") if isinstance(result.get("authoringCoherence"), dict) else {}
    coverage = result.get("gateCoverage") or coherence.get("gateCoverage") or []
    return write_markdown(
        layout.workflow_stage_document_path(project, alias, stage),
        f"Validation Summary: {alias}",
        {
            "Status": result.get("status"),
            "Selected Main Skill": result.get("selectedMainSkill"),
            "Core Status": result.get("coreStatus") or result.get("core", {}).get("status"),
            "Coverage Status": result.get("coverageStatus") or coherence.get("status"),
            "Gate Coverage": _render_gate_coverage(coverage),
            "Runtime Contradictions": _render_runtime_contradictions(result.get("runtimeContradictions", [])),
        },
    )


def _render_understanding_metadata(metadata: dict[str, Any]) -> list[str]:
    if not metadata:
        return []
    return [
        f"Generated At: {metadata.get('generatedAt', 'Not recorded')}",
        f"Generated Git Hash: {metadata.get('generatedGitHash') or 'Unavailable'}",
        f"Git Available: {str(metadata.get('gitAvailable', False)).lower()}",
        f"Inventory Status: {metadata.get('inventoryStatus', 'Not recorded')}",
        f"Source Traceability Status: {metadata.get('sourceTraceabilityStatus', 'Not recorded')}",
        f"Candidate Count: {metadata.get('candidateCount', 'Not recorded')}",
        f"Trivial Candidate Count: {metadata.get('trivialCandidateCount', 'Not recorded')}",
        f"Partial Inventory Reasons: {', '.join(metadata.get('partialInventoryReasons', [])) or 'None'}",
        f"Stale Reasons: {', '.join(metadata.get('staleReasons', [])) or 'None'}",
    ]


def _stage_contract_note(stage: str) -> str:
    return f"See stagePayloadContracts.{stage} from `proofsignal workflow info proofsignal-use-case --json`."


def _render_candidate_use_cases(candidates: list[dict[str, Any]]) -> list[str]:
    if not candidates:
        return ["No candidate validation use cases could be inferred from safe repository context."]
    rendered: list[str] = []
    for candidate in candidates:
        alias = candidate.get("alias") or candidate.get("candidateAlias") or "candidate"
        title = candidate.get("title") or candidate.get("behavior") or alias
        rationale = candidate.get("rationale", "No rationale recorded.")
        confidence = candidate.get("confidence", "medium")
        source_status = candidate.get("inventorySourceStatus")
        source = f", inventory: {source_status}" if source_status else ""
        rendered.append(f"{alias}: {title} ({confidence}{source}) - {rationale}")
    return rendered


def _render_gate_coverage(coverage: list[dict[str, Any]]) -> list[str]:
    if not coverage:
        return ["No gate coverage recorded."]
    rendered = []
    for item in coverage:
        rendered.append(
            f"{item.get('gateId')}: {item.get('status')}"
            + (f" ({item.get('conditionEvaluation')}: {item.get('condition')})" if item.get("condition") else "")
            + (f" - {item.get('notes')}" if item.get("notes") else "")
        )
    return rendered


def _render_runtime_inputs(runtime_inputs: list[dict[str, Any]]) -> list[str]:
    if not runtime_inputs:
        return []
    rendered: list[str] = []
    for item in runtime_inputs:
        if not isinstance(item, dict):
            rendered.append(str(item))
            continue
        name = item.get("name", "runtimeInput")
        value = item.get("value") or item.get("default") or item.get("valueRef")
        if value and str(name).lower() in {"baseurl", "targeturl", "url"}:
            rendered.append(f"{name}: resolved target ({value})")
        else:
            rendered.append(str(name))
    return rendered


def _render_skill_composition(composition: dict[str, Any] | None) -> list[str]:
    if not composition:
        return []
    rendered: list[str] = []
    mode = composition.get("mode")
    if mode:
        rendered.append(f"mode: {mode}")
    main = composition.get("mainSkillPath")
    if main:
        rendered.append(f"mainSkillPath: {main}")
    sources = composition.get("sourceSkillPaths")
    if isinstance(sources, list) and sources:
        rendered.append("sourceSkillPaths: " + ", ".join(str(item) for item in sources))
    policy = composition.get("credentialReferencePolicy")
    if policy:
        rendered.append(f"credentialReferencePolicy: {policy}")
    return rendered or [str(composition)]


def _render_gate_evidence_mappings(mappings: list[dict[str, Any]]) -> list[str]:
    rendered: list[str] = []
    for item in mappings:
        source = item.get("sourceSkillPath") or item.get("source")
        source_gate = item.get("sourceGateId") or item.get("sourceGate")
        gate = item.get("gateId") or item.get("targetGateId")
        if source or source_gate or gate:
            rendered.append(f"{source or 'source'}:{source_gate or '*'} -> {gate or 'gate'}")
        else:
            rendered.append(str(item))
    return rendered


def _render_runtime_contradictions(contradictions: list[dict[str, Any]]) -> list[str]:
    if not contradictions:
        return ["None recorded."]
    return [
        f"{item.get('gateId')}: {item.get('observedEvidence')} -> {item.get('recommendation')}"
        for item in contradictions
    ]
