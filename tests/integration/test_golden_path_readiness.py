from __future__ import annotations

from pathlib import Path


def test_quickstart_lists_golden_path_readiness_commands() -> None:
    content = Path("specs/009-golden-path-productization/quickstart.md").read_text(encoding="utf-8")

    assert "test_golden_path_readiness_contract.py" in content
    assert "test_golden_path_readiness.py" in content
    assert "ready to demo" in content.lower()
    assert "ready to release" in content.lower()
