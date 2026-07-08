from __future__ import annotations

from verifysignal_spec.workflows.coverage_inventory import inventory_needs_more_coverage, normalize_inventory


def test_partial_inventory_more_scenarios_requires_follow_up_pass() -> None:
    inventory = normalize_inventory(
        {
            "items": [
                {"id": "route-search", "surfaceType": "route", "path": "/search", "title": "Search"},
                {"id": "route-admin", "surfaceType": "route", "path": "/admin", "title": "Admin", "inventoryStatus": "uncovered"},
            ],
            "candidateUseCases": [
                {
                    "alias": "search",
                    "surface": "/search",
                    "behavior": "Validate search.",
                    "sourceInventoryItems": ["route-search"],
                    "rationale": "Public cross-entity surface.",
                    "confidence": "high",
                }
            ],
        },
        scope="all",
    )
    assert inventory.status == "partial"
    assert inventory_needs_more_coverage(inventory.to_dict())
    assert inventory.candidateUseCases[0].inventorySourceStatus == "partial"


def test_stale_inventory_recommends_refresh_behavior() -> None:
    inventory = normalize_inventory(
        {
            "staleAreas": ["app/search"],
            "items": [
                {"id": "route-search", "surfaceType": "route", "path": "/search", "title": "Search", "inventoryStatus": "stale"},
            ],
            "candidateUseCases": [],
        },
        scope="changed",
    )
    assert inventory.status == "stale"
    assert inventory_needs_more_coverage(inventory.to_dict())
