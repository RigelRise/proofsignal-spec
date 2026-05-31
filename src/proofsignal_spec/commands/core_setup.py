from __future__ import annotations

from pathlib import Path
from typing import Any

from proofsignal_spec.workflows.core_setup import run_core_setup


def run(project: Path, core_cmd: str | None = None, *, persist: bool = True) -> dict[str, Any]:
    return run_core_setup(project, explicit_core_cmd=core_cmd, persist=persist).to_dict()
