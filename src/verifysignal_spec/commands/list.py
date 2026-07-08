from __future__ import annotations

from pathlib import Path
from typing import Any

from verifysignal_spec.workspace.repository import list_use_cases


def run(project: Path) -> dict[str, Any]:
    rows, warnings = list_use_cases(project)
    return {"schemaVersion": "verifysignal-spec-list/v1", "useCases": rows, "warnings": warnings}
