from __future__ import annotations

from pathlib import Path


def test_spec_does_not_import_private_core_packages_or_source() -> None:
    src = Path("src/proofsignal_spec")
    offenders: list[str] = []
    private_markers = ("proofsignal_core", "from proofsignal.core", "import proofsignal.core")
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in private_markers):
            offenders.append(str(path))

    assert offenders == []


def test_spec_does_not_read_core_source_for_executable_contracts() -> None:
    src = Path("src/proofsignal_spec")
    offenders: list[str] = []
    source_markers = ("site-packages/proofsignal", "node_modules/proofsignal", "proofsignal-core/src", "Core source")
    for path in src.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        if any(marker in text for marker in source_markers):
            offenders.append(str(path))

    assert offenders == []
