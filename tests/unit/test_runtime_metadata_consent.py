from __future__ import annotations

import json
from pathlib import Path

from verifysignal_spec.runtime.consent import metadata_summary, resolve_metadata_consent


def test_metadata_summary_excludes_forbidden_categories(tmp_path: Path) -> None:
    summary = metadata_summary(tmp_path)
    text = json.dumps(summary)

    assert "source code" not in text.lower()
    assert "screenshot" not in text.lower()
    assert "browser storage" not in text.lower()
    assert "credentials" not in text.lower()
    assert summary["categories"]


def test_declined_metadata_consent_does_not_block_runtime_unlock(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_METADATA_CONSENT", "declined")

    decision = resolve_metadata_consent(tmp_path)

    assert decision.status == "declined"
    assert decision.blocksRuntimeUnlock is False

