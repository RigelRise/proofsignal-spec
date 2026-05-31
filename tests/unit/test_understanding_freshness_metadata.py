from __future__ import annotations

from proofsignal_spec.workspace.product_context import (
    load_product_context,
    record_understanding_refresh_decision,
    save_product_context,
)
from proofsignal_spec.workspace.repository import init_workspace, now_iso
from proofsignal_spec.workflows.prerequisites import check_prerequisites

from tests.fixtures.workflows.prerequisites import (
    create_current_understanding_workspace,
    create_git_workspace_with_stale_commit,
    create_stale_understanding_workspace,
    sample_candidate,
)


def test_product_context_rejects_secret_looking_candidate_values(tmp_path) -> None:
    init_workspace(tmp_path)
    context = load_product_context(tmp_path)
    context["understanding"] = {
        "generatedAt": now_iso(),
        "generatedGitHash": None,
        "gitAvailable": False,
        "staleReasons": [],
    }
    context["candidateUseCases"] = [{**sample_candidate(), "apiKey": "real-secret-value"}]
    try:
        save_product_context(tmp_path, context)
    except ValueError as exc:
        assert "Secret-looking product context value" in str(exc)
    else:
        raise AssertionError("Expected product context secret validation to reject apiKey")


def test_declined_refresh_records_only_reason_codes(tmp_path) -> None:
    init_workspace(tmp_path)
    record_understanding_refresh_decision(
        tmp_path,
        "declined",
        [{"code": "age", "message": "Bearer real-secret-token-123456789"}],
        stage="specify",
    )
    context = load_product_context(tmp_path)
    understanding = context["understanding"]
    assert understanding["refreshDeclinedReasons"] == ["age"]
    assert "Bearer" not in str(context)
    assert understanding["refreshDecision"]["decision"] == "declined"


def test_current_understanding_returns_candidates_and_first_run_recommendation_command(tmp_path) -> None:
    create_current_understanding_workspace(tmp_path, candidates=[sample_candidate("checkout")])
    result = check_prerequisites(tmp_path, "specify")
    assert result["status"] == "ready"
    assert result["canProceed"] is True
    assert result["candidateUseCases"][0]["candidateAlias"] == "checkout"
    assert result["recommendedCandidate"]["candidateAlias"] == "checkout"
    assert result["candidateSelectionSource"] == "workflow.recommend-first-run"
    assert result["firstRunRecommendationCommand"] == "proofsignal-spec workflow recommend-first-run --json"
    assert result["projectOverview"]


def test_stale_understanding_by_age_updates_stale_reason_codes(tmp_path) -> None:
    create_stale_understanding_workspace(tmp_path)
    result = check_prerequisites(tmp_path, "specify")
    assert result["status"] == "stale"
    assert result["requiresConfirmation"] is True
    assert [item["code"] for item in result["staleReasons"]] == ["age"]
    context = load_product_context(tmp_path)
    assert context["understanding"]["staleReasons"] == ["age"]


def test_stale_understanding_by_commit_distance(tmp_path) -> None:
    create_git_workspace_with_stale_commit(tmp_path)
    result = check_prerequisites(tmp_path, "specify")
    assert result["status"] == "stale"
    assert "commit-distance" in [item["code"] for item in result["staleReasons"]]
