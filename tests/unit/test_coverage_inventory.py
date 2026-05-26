from __future__ import annotations

import pytest

from proofsignal_spec.workflows.coverage_inventory import merge_inventory, normalize_inventory


def test_inventory_complete_requires_covered_or_excluded_user_facing_items() -> None:
    inventory = normalize_inventory(
        {
            "items": [
                {
                    "id": "route-login",
                    "surfaceType": "route",
                    "path": "/login",
                    "title": "Login",
                    "inventoryStatus": "covered",
                }
            ],
            "candidateUseCases": [],
        },
        scope="all",
    )
    assert inventory.status == "complete"

    partial = normalize_inventory(
        {
            "items": [
                {
                    "id": "route-login",
                    "surfaceType": "route",
                    "path": "/login",
                    "title": "Login",
                    "inventoryStatus": "uncovered",
                }
            ],
            "candidateUseCases": [],
        },
        scope="all",
    )
    assert partial.status == "partial"


def test_excluded_inventory_items_require_reason() -> None:
    with pytest.raises(ValueError, match="requires exclusionReason"):
        normalize_inventory(
            {
                "items": [
                    {
                        "id": "route-admin",
                        "surfaceType": "route",
                        "path": "/admin",
                        "title": "Admin",
                        "inventoryStatus": "excluded",
                    }
                ]
            },
            scope="all",
        )


def test_candidate_use_cases_can_infer_inventory_provenance_from_surface() -> None:
    inventory = normalize_inventory(
        {
            "items": [
                {
                    "id": "route-search",
                    "surfaceType": "route",
                    "path": "/search",
                    "title": "Search",
                }
            ],
            "candidateUseCases": [
                {
                    "alias": "search",
                    "surface": "/search",
                    "behavior": "Validate search.",
                    "rationale": "High-value flow.",
                }
            ],
        },
        scope="all",
    )
    assert inventory.candidateUseCases[0].sourceInventoryItems == ["route-search"]


def test_understand_payload_covered_areas_are_flattened_to_inventory_items() -> None:
    inventory = normalize_inventory(
        {
            "coveredAreas": [
                {
                    "area": "search",
                    "surfaces": [
                        {"route": "/search/people", "type": "page", "description": "People search"},
                    ],
                }
            ],
            "candidateUseCases": [
                {
                    "alias": "search-people",
                    "description": "Validate people search.",
                    "surface": "/search/people",
                }
            ],
        },
        scope="all",
    )
    assert inventory.items[0].path == "/search/people"
    assert inventory.candidateUseCases[0].sourceInventoryItems == [inventory.items[0].id]


def test_continue_scope_merges_without_replacing_unrelated_items() -> None:
    existing = {
        "items": [
            {"id": "route-a", "surfaceType": "route", "path": "/a", "title": "A"},
        ],
        "uncoveredAreas": ["app/b"],
    }
    incoming = {
        "items": [
            {"id": "route-b", "surfaceType": "route", "path": "/b", "title": "B"},
        ],
        "candidateUseCases": [],
    }
    merged = merge_inventory(existing, incoming, scope="continue")
    assert {item.id for item in merged.items} == {"route-a", "route-b"}
    assert "app/b" in merged.uncoveredAreas
