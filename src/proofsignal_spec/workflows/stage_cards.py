from __future__ import annotations

from typing import Any

from .models import AgentChatStageCard


def build_stage_card(
    *,
    stage_id: str,
    title: str,
    status_marker: str,
    summary: str,
    why_it_matters: str,
    primary_evidence: str,
    next_action: str,
    repair_details: str | None = None,
    secondary_refs: list[str] | None = None,
) -> AgentChatStageCard:
    return AgentChatStageCard(
        stageId=stage_id,
        title=title,
        statusMarker=status_marker,  # type: ignore[arg-type]
        summary=summary,
        whyItMatters=why_it_matters,
        primaryEvidence=primary_evidence,
        nextAction=next_action,
        repairDetails=repair_details,
        secondaryRefs=secondary_refs or [],
    )


def recommendation_card(alias: str, rationale: str, *, next_action: str) -> dict[str, Any]:
    return build_stage_card(
        stage_id="first-run-recommendation",
        title="Recommended First Run",
        status_marker="[RECOMMENDED]",
        summary=f"{alias} is the recommended first validation.",
        why_it_matters="Starting with the simplest stable real target lets the user see ProofSignal work end to end.",
        primary_evidence=rationale,
        next_action=next_action,
    ).to_dict()


def acceptance_card(alias: str, *, next_action: str) -> dict[str, Any]:
    return build_stage_card(
        stage_id="first-run-accepted",
        title="First Run Accepted",
        status_marker="[ACCEPTED]",
        summary=f"{alias} is now the selected golden-path first run.",
        why_it_matters="The accepted candidate is the product's first-run success metric.",
        primary_evidence=f"Selected candidate: {alias}",
        next_action=next_action,
    ).to_dict()


def skip_card(*, next_action: str) -> dict[str, Any]:
    return build_stage_card(
        stage_id="first-run-skipped",
        title="First Run Skipped",
        status_marker="[SKIPPED]",
        summary="The recommended first run was skipped.",
        why_it_matters="Skipping is tracked separately from pass, fail, or incomplete.",
        primary_evidence="The user declined the recommended golden-path candidate.",
        next_action=next_action,
    ).to_dict()


def blocker_card(title: str, summary: str, evidence: str, *, next_action: str) -> dict[str, Any]:
    return build_stage_card(
        stage_id="first-run-blocked",
        title=title,
        status_marker="[BLOCKED]",
        summary=summary,
        why_it_matters="The first run must start from a reliable real target and safe workspace state.",
        primary_evidence=evidence,
        next_action=next_action,
    ).to_dict()


def run_result_card(
    *,
    alias: str,
    first_run_status: str,
    strict_pass: bool,
    core_browser_status: str,
    spec_coverage_status: str,
    missing_required_gates: list[str],
    next_action: str,
) -> dict[str, Any]:
    marker = "[PASS]" if strict_pass else ("[BLOCKED]" if first_run_status == "blocked" else "[FAIL]")
    evidence = (
        f"coreBrowserStatus={core_browser_status}; specCoverageStatus={spec_coverage_status}; "
        f"missingRequiredGates={missing_required_gates}"
    )
    return build_stage_card(
        stage_id="first-run-result",
        title="First Run Result",
        status_marker=marker,
        summary=f"{alias} finished with firstRunStatus={first_run_status}.",
        why_it_matters="The first-run metric succeeds only on strict pass or repaired strict pass.",
        primary_evidence=evidence,
        next_action=next_action,
    ).to_dict()


def repair_stage_card(
    *,
    category: str,
    autonomy: str,
    before: str,
    after: str,
    next_action: str,
) -> dict[str, Any]:
    return build_stage_card(
        stage_id="first-run-repair",
        title="Repair Decision",
        status_marker="[REPAIR]",
        summary=f"{category} repair is {autonomy}.",
        why_it_matters="Safe mechanical repair should show exactly what changed before a trusted rerun.",
        primary_evidence=f"Before: {before}",
        repair_details=f"After: {after}",
        next_action=next_action,
    ).to_dict()
