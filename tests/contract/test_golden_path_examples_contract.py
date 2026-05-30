from __future__ import annotations

from pathlib import Path


def test_golden_path_docs_cover_four_canonical_examples() -> None:
    content = Path("docs/golden-path.md").read_text(encoding="utf-8")

    for heading in [
        "Public Unauthenticated Example",
        "Authenticated Secret-Safe Example",
        "Repairable Failure Example",
        "Conditional Data Example",
    ]:
        assert heading in content

    for term in ["Expected outcome", "Failure modes", "Evidence expectations", "pass", "fail", "not-evaluated"]:
        assert term in content

    assert "fake/demo" in content
    assert "fallback" in content
