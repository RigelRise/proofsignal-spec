from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from proofsignal_spec.workspace import layout
from proofsignal_spec.workspace.repository import load_document, load_use_case, now_iso
from proofsignal_spec.workspace.validation import looks_secret, validate_no_secret_values

from .models import (
    CandidateValidationUseCase,
    FirstRunCandidate,
    FirstRunCandidateScore,
    FirstRunRecommendation,
    GoldenPathRunState,
)
from .stage_cards import acceptance_card, blocker_card, recommendation_card, skip_card
from .repository import load_golden_path_state, save_golden_path_state


GOLDEN_PATH_STATE_SCHEMA = "proofsignal-spec-golden-path-state/v1"


def classify_first_run_status(
    core_browser_status: str,
    spec_coverage_status: str,
    missing_required_gates: list[str],
    *,
    repaired: bool = False,
) -> tuple[str, bool]:
    if core_browser_status in {"blocked", "error"}:
        return "blocked", False
    if core_browser_status != "passed":
        return "failed", False
    if spec_coverage_status not in {"complete", "passed"} or missing_required_gates:
        return "incomplete", False
    return ("repaired-passed" if repaired else "passed"), True


def score_first_run_candidates(
    candidates: list[CandidateValidationUseCase | FirstRunCandidate],
    *,
    target_status: str = "unknown",
    inventory_status: str = "partial",
) -> list[FirstRunCandidateScore]:
    scored: list[FirstRunCandidateScore] = []
    for candidate in candidates:
        first_run_candidate = (
            candidate if isinstance(candidate, FirstRunCandidate) else FirstRunCandidate.from_candidate_use_case(candidate)
        )
        requirements = [item.lower() for item in first_run_candidate.knownRuntimeRequirements]
        blockers: list[str] = []
        low_setup = 25 if not any("credential" in item for item in requirements) else 5
        target = 20 if target_status == "resolved" else 0
        if target_status != "resolved":
            blockers.append("Real target is not resolved.")
        credential_risk = 0
        if any(_requires_credential(item) for item in requirements):
            credential_risk = -30
            blockers.append("Unresolved credentials are not suitable for the first run.")
        rendered = 20 if _simple_rendered_evidence(first_run_candidate) else 10
        data_risk = -15 if _data_dependent(requirements, first_run_candidate.behavior) else 0
        freshness = 10 if inventory_status == "complete" else (4 if inventory_status == "partial" else 0)
        priority = {"critical": 20, "high": 15, "medium": 8, "low": 3}.get(first_run_candidate.priority, 8)
        confidence = {"high": 5, "medium": 2, "low": 0}.get(first_run_candidate.confidence, 2)
        raw_score = low_setup + target + rendered + data_risk + freshness + priority + confidence + credential_risk
        score = max(0, min(100, raw_score))
        scored.append(
            FirstRunCandidateScore(
                candidateAlias=first_run_candidate.alias,
                rank=0,
                score=score,
                lowSetupRisk=low_setup,
                reachableRealTarget=target,
                credentialRisk=credential_risk,
                renderedEvidenceSimplicity=rendered,
                dataDependencyRisk=data_risk,
                inventoryFreshness=freshness,
                rationale=_rationale(first_run_candidate, blockers),
                blockers=blockers,
                candidate=first_run_candidate,
            )
        )
    scored.sort(key=lambda item: (item.blockers != [], -item.score, item.candidateAlias))
    for index, item in enumerate(scored, start=1):
        item.rank = index
    return scored


def build_first_run_recommendation(project: Path) -> FirstRunRecommendation:
    context = load_document(layout.product_context_path(project), default={}) or {}
    inventory = context.get("coverageInventory") if isinstance(context.get("coverageInventory"), dict) else {}
    candidates = [
        CandidateValidationUseCase.from_dict(item, str(inventory.get("status", "partial")))
        for item in inventory.get("candidateUseCases", [])
        if isinstance(item, dict)
    ]
    target_status, target_locator = resolve_target_status(context)
    if not candidates:
        return _blocked_recommendation("No coverage inventory candidates were found.", "Run /proofsignal-understand first.")
    ranked = score_first_run_candidates(candidates, target_status=target_status, inventory_status=str(inventory.get("status", "partial")))
    top = next((item for item in ranked if not item.blockers), None)
    if not top or target_status != "resolved":
        code = "unreachable-target" if target_status == "unreachable" else "missing-target"
        blocker = classify_first_run_blocker(code)
        next_action = blocker["nextAction"]
        return FirstRunRecommendation(
            status="blocked",
            targetStatus=target_status,  # type: ignore[arg-type]
            rankedCandidates=[item.to_dict() for item in ranked],
            recommendationText="A reliable real-target first run cannot be recommended yet.",
            acceptancePrompt="Resolve the blocker before accepting a first run.",
            stageCards=blocker["stageCards"],
            nextAction=next_action,
        )
    candidate = top.candidate or FirstRunCandidate(alias=top.candidateAlias, surface="", behavior="")
    recommended = {
        "alias": candidate.alias,
        "surface": candidate.surface,
        "behavior": candidate.behavior,
        "score": top.score,
        "rationale": top.rationale,
        "sourceInventoryItems": candidate.sourceInventoryItems,
        "knownRuntimeRequirements": candidate.knownRuntimeRequirements,
    }
    next_action = f"proofsignal-spec workflow accept-first-run {candidate.alias} --json"
    text = (
        f"I strongly recommend starting with {candidate.alias}. It is the simplest stable real-target validation "
        "for the first run; after it passes, choose any deeper use case."
    )
    return FirstRunRecommendation(
        status="ready",
        targetStatus=target_status,  # type: ignore[arg-type]
        recommendedCandidate=recommended,
        rankedCandidates=[item.to_dict() for item in ranked],
        recommendationText=text,
        acceptancePrompt=(
            "Accepting this first run is highly recommended so you can see the ProofSignal workflow end to end. "
            "You can choose other validations afterward."
        ),
        stageCards=[recommendation_card(candidate.alias, top.rationale, next_action=next_action)],
        nextAction=next_action,
    )


def accept_first_run(project: Path, alias: str) -> dict[str, Any]:
    record = load_use_case(project, alias)
    state = {
        "schemaVersion": GOLDEN_PATH_STATE_SCHEMA,
        "acceptedAt": now_iso(),
        "selectedCandidate": alias,
        "firstRunStatus": "not-started",
        "recommendationStatus": "accepted",
    }
    _write_state(project, state)
    next_action = f"proofsignal-spec run {alias} --json"
    return {
        "schemaVersion": "proofsignal-spec-first-run-recommendation/v1",
        "status": "accepted",
        "selectedCandidate": {
            "alias": record.alias,
            "surface": record.targetSurface,
            "behavior": record.description,
        },
        "stageCards": [acceptance_card(alias, next_action=next_action)],
        "nextAction": next_action,
    }


def skip_first_run(project: Path) -> dict[str, Any]:
    state = {
        "schemaVersion": GOLDEN_PATH_STATE_SCHEMA,
        "skippedAt": now_iso(),
        "firstRunStatus": "skipped",
        "recommendationStatus": "skipped",
    }
    _write_state(project, state)
    next_action = "Use /proofsignal-specify <custom use case> when you are ready."
    skip_meaning = "Skipping records that the golden path was declined; it is not success, failure, or inconclusive."
    return {
        "schemaVersion": "proofsignal-spec-first-run-recommendation/v1",
        "status": "skipped",
        "skipMeaning": skip_meaning,
        "stageCards": [skip_card(next_action=next_action)],
        "nextAction": next_action,
    }


def golden_path_state(project: Path) -> dict[str, Any]:
    return load_golden_path_state(project)


def update_golden_path_run_state(project: Path, state: GoldenPathRunState) -> None:
    current = golden_path_state(project)
    current.update({"schemaVersion": GOLDEN_PATH_STATE_SCHEMA, "runState": state.to_dict(), "firstRunStatus": state.firstRunStatus})
    _write_state(project, current)


def summarize_target(value: str) -> str:
    if not value:
        return ""
    if looks_secret(value, "target"):
        return "[redacted-sensitive-target]"
    return value


def summarize_evidence(value: str) -> str:
    if looks_secret(value, "evidence"):
        return "[redacted-sensitive-evidence]"
    text = " ".join(str(value).split())
    return text[:240]


def resolve_target_status(context: dict[str, Any]) -> tuple[str, str | None]:
    for item in context.get("knownRuntimeRequirements", []):
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "")).lower()
        value = str(item.get("value") or item.get("default") or "")
        if name in {"baseurl", "target", "targeturl"} and value:
            if looks_secret(value, name):
                return "missing", None
            if _looks_fake_or_demo(value):
                return "missing", None
            if _looks_unreachable(value):
                return "unreachable", summarize_target(value)
            return "resolved", summarize_target(value)
    return "missing", None


def classify_first_run_blocker(code: str, *, alias: str | None = None) -> dict[str, Any]:
    catalog = {
        "missing-target": (
            "missing-target",
            "The first run needs a confirmed real browser target before it can be recommended.",
            "/proofsignal-clarify <alias>",
        ),
        "unreachable-target": (
            "unreachable-target",
            "The selected target is known or likely unreachable from this environment.",
            "Confirm the target URL or start the app, then rerun recommend-first-run.",
        ),
        "unresolved-credentials": (
            "unresolved-credentials",
            "All available candidates require credentials that are not resolved as runtime references.",
            "Choose a public candidate or resolve credential references without persisting values.",
        ),
        "stale-inventory": (
            "stale-inventory",
            "Coverage inventory is stale and cannot support a reliable first-run recommendation.",
            "/proofsignal-understand --scope changed",
        ),
        "stale-workspace": (
            "stale-workspace",
            "Golden Path workspace state is older than the supported schema.",
            "proofsignal-spec workflow inspect-golden-path-state --json",
        ),
        "incompatible-core": (
            "incompatible-core",
            "Configured ProofSignal Core does not expose the required public CLI JSON operations.",
            "proofsignal-spec core version --json",
        ),
    }
    category, summary, next_action = catalog.get(code, ("unknown-blocker", "The first run is blocked.", "/proofsignal-list"))
    evidence = f"{category}: {summary}"
    return {
        "status": "blocked",
        "category": category,
        "alias": alias,
        "summary": summary,
        "stageCards": [blocker_card("First Run Blocked", summary, evidence, next_action=next_action)],
        "nextAction": next_action,
    }


def _write_state(project: Path, data: dict[str, Any]) -> None:
    findings = validate_no_secret_values(data)
    if findings:
        first = findings[0]
        raise ValueError(f"Secret-looking first-run state value at {first.get('path')}: {first.get('message')}")
    save_golden_path_state(project, data)


def _blocked_recommendation(summary: str, next_action: str) -> FirstRunRecommendation:
    return FirstRunRecommendation(
        status="blocked",
        targetStatus="missing",
        recommendationText="A first run cannot be recommended yet.",
        acceptancePrompt="Resolve the blocker before accepting a first run.",
        stageCards=[blocker_card("First Run Blocked", summary, summary, next_action=next_action)],
        nextAction=next_action,
    )


def _requires_credential(requirement: str) -> bool:
    return any(term in requirement for term in ["credential", "password", "auth", "login", "secret"])


def _simple_rendered_evidence(candidate: FirstRunCandidate) -> bool:
    text = f"{candidate.surface} {candidate.behavior}".lower()
    return any(term in text for term in ["public", "home", "page", "render", "unauth"])


def _data_dependent(requirements: list[str], behavior: str) -> bool:
    text = " ".join(requirements + [behavior.lower()])
    return any(term in text for term in ["seed", "data", "conditional", "activity", "empty"])


def _looks_fake_or_demo(value: str) -> bool:
    parsed = urlsplit(value)
    host = (parsed.hostname or value).lower()
    return any(term in host for term in ["example.com", "demo", "fake", "localhost.demo"])


def _looks_unreachable(value: str) -> bool:
    parsed = urlsplit(value)
    return parsed.hostname in {"127.0.0.1", "0.0.0.0"} and parsed.port == 9


def _rationale(candidate: FirstRunCandidate, blockers: list[str]) -> str:
    if blockers:
        return f"{candidate.alias} is blocked for first run: {' '.join(blockers)}"
    return (
        f"{candidate.alias} is suitable because it targets {candidate.surface or 'a real surface'}, "
        f"has {candidate.confidence} confidence, {candidate.priority} priority, and simple rendered evidence."
    )
