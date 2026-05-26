from __future__ import annotations

from typing import Any
import re

from .models import CoverageInventory, CoverageInventoryItem, CandidateValidationUseCase, InventoryPass

VALID_SCOPES = {"all", "changed", "continue"}
SURFACE_PRIORITY = {
    "route": 0,
    "page": 0,
    "flow": 1,
    "form": 1,
    "action": 1,
    "permission": 2,
    "state": 2,
    "integration": 2,
}


def normalize_scope(scope: str | None) -> str:
    value = scope or "all"
    if value in VALID_SCOPES or value.startswith("route:") or value.startswith("area:"):
        return value
    raise ValueError("Scope must be all, changed, continue, route:<path>, or area:<name>.")


def normalize_inventory(data: dict[str, Any] | None, *, scope: str | None = None) -> CoverageInventory:
    payload = dict(data or {})
    normalize_scope(scope)
    payload = _normalize_inventory_payload(payload)
    if "items" not in payload:
        payload["items"] = []
    if "candidateUseCases" not in payload:
        payload["candidateUseCases"] = []
    inventory = CoverageInventory.from_dict(payload)
    inventory.items = sorted(
        inventory.items,
        key=lambda item: (SURFACE_PRIORITY.get(item.surfaceType, 3), _priority_rank(item.priority), item.path, item.id),
    )
    _validate_inventory(inventory)
    inventory.status = _computed_status(inventory)
    return inventory


def _normalize_inventory_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not payload.get("items") and isinstance(payload.get("coveredAreas"), list):
        items: list[dict[str, Any]] = []
        for area in payload.get("coveredAreas", []):
            if not isinstance(area, dict):
                continue
            area_name = str(area.get("area") or area.get("name") or "area")
            for surface in area.get("surfaces", []):
                if not isinstance(surface, dict):
                    continue
                path = str(surface.get("route") or surface.get("path") or surface.get("container") or surface.get("name") or "")
                if not path:
                    continue
                item_id = surface.get("id") or f"{_slug(area_name)}-{_slug(path)}"
                items.append(
                    {
                        "id": item_id,
                        "surfaceType": surface.get("type") or ("route" if surface.get("route") else "flow"),
                        "path": path,
                        "title": surface.get("title") or surface.get("description") or path,
                        "sourceRefs": surface.get("sourceRefs", []),
                        "userFacing": surface.get("userFacing", True),
                        "inventoryStatus": surface.get("inventoryStatus", "covered"),
                        "exclusionReason": surface.get("exclusionReason"),
                        "candidateUseCaseRefs": surface.get("candidateUseCaseRefs", []),
                        "priority": surface.get("priority", "medium"),
                    }
                )
        payload["items"] = items
    if "uncoveredAreas" not in payload and isinstance(payload.get("uncovered"), list):
        payload["uncoveredAreas"] = payload["uncovered"]
    items = payload.get("items", [])
    item_ids = [str(item.get("id")) for item in items if isinstance(item, dict) and item.get("id")]
    normalized_candidates: list[dict[str, Any]] = []
    for candidate in payload.get("candidateUseCases", []):
        if not isinstance(candidate, dict):
            continue
        normalized = dict(candidate)
        if not normalized.get("sourceInventoryItems"):
            normalized["sourceInventoryItems"] = _candidate_sources(normalized, items, item_ids)
        if not normalized.get("rationale"):
            normalized["rationale"] = normalized.get("description") or normalized.get("behavior") or "Candidate inferred from repository understanding."
        if not normalized.get("behavior"):
            normalized["behavior"] = normalized.get("description") or normalized.get("title") or normalized.get("alias", "")
        normalized_candidates.append(normalized)
    payload["candidateUseCases"] = normalized_candidates
    return payload


def merge_inventory(existing: dict[str, Any] | None, incoming: dict[str, Any] | None, *, scope: str | None = None) -> CoverageInventory:
    normalize_scope(scope)
    if not existing:
        return normalize_inventory(incoming, scope=scope)
    current = CoverageInventory.from_dict(existing)
    update = normalize_inventory(incoming, scope=scope)

    items_by_id = {item.id: item for item in current.items}
    for item in update.items:
        items_by_id[item.id] = item

    candidates_by_alias = {candidate.alias: candidate for candidate in current.candidateUseCases}
    for candidate in update.candidateUseCases:
        candidates_by_alias[candidate.alias] = candidate

    passes = [*current.passes, *update.passes]
    uncovered = sorted({*current.uncoveredAreas, *update.uncoveredAreas})
    stale = sorted({*current.staleAreas, *update.staleAreas})

    merged = CoverageInventory(
        status=update.status,
        generatedAt=update.generatedAt or current.generatedAt,
        generatedGitHash=update.generatedGitHash or current.generatedGitHash,
        gitAvailable=update.gitAvailable or current.gitAvailable,
        passes=passes,
        items=list(items_by_id.values()),
        candidateUseCases=list(candidates_by_alias.values()),
        uncoveredAreas=uncovered,
        staleAreas=stale,
    )
    merged.items = sorted(
        merged.items,
        key=lambda item: (SURFACE_PRIORITY.get(item.surfaceType, 3), _priority_rank(item.priority), item.path, item.id),
    )
    _validate_inventory(merged)
    merged.status = _computed_status(merged)
    return merged


def candidate_dicts(inventory: CoverageInventory) -> list[dict[str, Any]]:
    return [candidate.to_dict() for candidate in inventory.candidateUseCases]


def inventory_needs_more_coverage(inventory_data: dict[str, Any] | None) -> bool:
    if not inventory_data:
        return True
    status = inventory_data.get("status", "partial")
    return status in {"partial", "stale"}


def _validate_inventory(inventory: CoverageInventory) -> None:
    item_ids = {item.id for item in inventory.items if item.id}
    for item in inventory.items:
        if not item.id:
            raise ValueError("Coverage inventory items require id.")
        if item.inventoryStatus == "excluded" and not item.exclusionReason:
            raise ValueError(f"Excluded inventory item {item.id} requires exclusionReason.")
    for candidate in inventory.candidateUseCases:
        if not candidate.alias:
            raise ValueError("Candidate validation use cases require alias.")
        if not candidate.rationale:
            raise ValueError(f"Candidate validation use case {candidate.alias} requires rationale.")
        if not candidate.sourceInventoryItems:
            raise ValueError(f"Candidate validation use case {candidate.alias} requires sourceInventoryItems.")
        missing = [item for item in candidate.sourceInventoryItems if item not in item_ids]
        if missing:
            raise ValueError(f"Candidate validation use case {candidate.alias} references unknown inventory items: {', '.join(missing)}.")


def _computed_status(inventory: CoverageInventory) -> str:
    if inventory.staleAreas or any(item.inventoryStatus == "stale" for item in inventory.items):
        return "stale"
    if inventory.uncoveredAreas:
        return "partial"
    if any(item.userFacing and item.inventoryStatus == "uncovered" for item in inventory.items):
        return "partial"
    if all(
        (not item.userFacing) or item.inventoryStatus == "covered" or (item.inventoryStatus == "excluded" and item.exclusionReason)
        for item in inventory.items
    ):
        return "complete" if inventory.items else "partial"
    return "partial"


def _priority_rank(priority: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(priority, 2)


def _candidate_sources(candidate: dict[str, Any], items: list[Any], item_ids: list[str]) -> list[str]:
    surface = str(candidate.get("surface") or candidate.get("targetSurface") or "")
    for item in items:
        if not isinstance(item, dict):
            continue
        path = str(item.get("path") or "")
        if path and surface and (path == surface or path in surface or surface in path):
            return [str(item.get("id"))]
    return item_ids[:1]


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-") or "item"
