from __future__ import annotations

import hashlib
import os
from pathlib import Path

from verifysignal_spec.workspace.repository import now_iso

from .models import MetadataConsentDecision


SAFE_METADATA_CATEGORIES = [
    "stack signals",
    "scenario categories",
    "coverage inventory status",
    "blocker categories",
    "validation outcome categories",
]


def metadata_summary(project: Path) -> dict[str, object]:
    summary_id = hashlib.sha256(str(project.resolve()).encode("utf-8")).hexdigest()[:12]
    return {
        "schemaVersion": "verifysignal-spec-metadata-summary/v1",
        "summaryId": summary_id,
        "categories": list(SAFE_METADATA_CATEGORIES),
        "forbiddenCategoriesExcluded": True,
    }


def resolve_metadata_consent(project: Path) -> MetadataConsentDecision:
    summary = metadata_summary(project)
    status = os.environ.get("VERIFYSIGNAL_METADATA_CONSENT", "not-asked").strip().lower()
    if status not in {"granted", "declined"}:
        status = "not-asked"
    return MetadataConsentDecision(
        status=status,  # type: ignore[arg-type]
        decidedAt=now_iso() if status in {"granted", "declined"} else None,
        summaryId=str(summary["summaryId"]),
        categories=[str(item) for item in summary["categories"]],
        blocksRuntimeUnlock=False,
    )

