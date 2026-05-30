from __future__ import annotations

from pathlib import Path


def test_release_readiness_docs_define_demo_and_release_criteria() -> None:
    content = Path("docs/release-readiness.md").read_text(encoding="utf-8").lower()

    assert "ready to demo" in content
    assert "ready to release" in content
    assert "pass/fail" in content
    for area in ["documentation", "examples", "workflow output", "troubleshooting", "secret", "core", "regression"]:
        assert area in content
