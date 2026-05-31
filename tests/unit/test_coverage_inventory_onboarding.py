from __future__ import annotations

import pytest

from proofsignal_spec.workflows.coverage_inventory import normalize_inventory


def test_candidate_sources_normalize_from_item_id_source_ref_and_surface_path() -> None:
    inventory = normalize_inventory(
        {
            "items": [
                {
                    "id": "route-project",
                    "surfaceType": "route",
                    "path": "/project/[path]",
                    "title": "Project",
                    "sourceRefs": ["app/(public)/project/[path]/page.tsx"],
                },
                {
                    "id": "route-home",
                    "surfaceType": "route",
                    "path": "/",
                    "title": "Home",
                    "sourceRefs": ["app/(public)/page.tsx"],
                },
            ],
            "candidateUseCases": [
                {
                    "alias": "project-view",
                    "surface": "/project/nike/campaign",
                    "behavior": "Project page renders.",
                    "rationale": "Surface match.",
                },
                {
                    "alias": "home-page",
                    "sourceRefs": ["app/(public)/page.tsx"],
                    "behavior": "Home page renders.",
                    "rationale": "Source ref match.",
                },
            ],
        },
        scope="all",
    )

    by_alias = {candidate.alias: candidate for candidate in inventory.candidateUseCases}
    assert by_alias["project-view"].sourceInventoryItems == ["route-project"]
    assert by_alias["home-page"].sourceInventoryItems == ["route-home"]


def test_missing_candidate_traceability_message_names_recovery_field() -> None:
    with pytest.raises(ValueError, match="sourceInventoryItems"):
        normalize_inventory(
            {
                "items": [],
                "candidateUseCases": [
                    {
                        "alias": "orphan",
                        "surface": "/missing",
                        "behavior": "Missing route.",
                        "rationale": "No traceability.",
                    }
                ],
            },
            scope="all",
        )
