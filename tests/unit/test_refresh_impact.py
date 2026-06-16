from __future__ import annotations

from proofsignal_spec.workspace.models import RefreshImpactResult
from proofsignal_spec.workspace.repository import load_refresh_impact, save_refresh_impact
from proofsignal_spec.workflows.coverage_inventory import classify_refresh_impacts


class _Record:
    def __init__(self, alias: str, target_surface: str) -> None:
        self.alias = alias
        self.targetSurface = target_surface


def test_refresh_impact_result_persists_unknown_without_guessing(tmp_path) -> None:
    save_refresh_impact(
        tmp_path,
        RefreshImpactResult(
            alias="add-collaboration-project",
            status="unknown",
            reason="Refreshed inventory changed but tested-code precision is unavailable.",
            affectedAreas=["tested-code-scope"],
            recommendedAction="validate",
        ),
    )

    result = load_refresh_impact(tmp_path, "add-collaboration-project")

    assert result
    assert result.status == "unknown"
    assert result.affectedAreas == ["tested-code-scope"]
    assert result.recommendedAction == "validate"


def test_classify_refresh_impact_preserves_unrelated_use_case() -> None:
    impacts = classify_refresh_impacts(
        {"items": [{"id": "route-about", "surfaceType": "route", "path": "/about", "title": "About"}]},
        {"items": [{"id": "route-search", "surfaceType": "route", "path": "/search", "title": "Search"}]},
        [_Record("about-page-unauth", "/about")],
        generated_at="2026-06-17T00:00:00Z",
    )

    assert impacts[0].alias == "about-page-unauth"
    assert impacts[0].status == "unaffected"
    assert impacts[0].recommendedAction == "none"


def test_classify_refresh_impact_marks_changed_target_surface_affected() -> None:
    impacts = classify_refresh_impacts(
        {"items": [{"id": "route-about", "surfaceType": "route", "path": "/about", "title": "About"}]},
        {"items": [{"id": "route-about", "surfaceType": "route", "path": "/about", "title": "About updated"}]},
        [_Record("about-page-unauth", "/about")],
        generated_at="2026-06-17T00:00:00Z",
    )

    assert impacts[0].status == "affected"
    assert impacts[0].affectedAreas == ["/about"]
    assert impacts[0].recommendedAction == "validate"
