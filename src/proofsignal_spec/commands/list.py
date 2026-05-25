from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.repository import list_use_cases


def run(project: Path) -> dict[str, Any]:
    rows, warnings = list_use_cases(project)
    return {"schemaVersion": "proofsignal-spec-list/v1", "useCases": rows, "warnings": warnings}
