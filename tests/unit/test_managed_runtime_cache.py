from __future__ import annotations

from pathlib import Path

from proofsignal_spec.runtime.cache import cache_root, load_cache_entry, save_cache_entry


def test_cache_metadata_lives_outside_target_project(tmp_path: Path, monkeypatch) -> None:
    project = tmp_path / "target"
    project.mkdir()
    user_cache = tmp_path / "user-cache"
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(user_cache))

    entry = save_cache_entry(
        core_version="0.12.0",
        platform="darwin-arm64",
        runtime_command=str(user_cache / "0.12.0" / "darwin-arm64" / "proofsignal-core"),
        contract_version="proofsignal-public-cli-json/v1",
        sha256="a" * 64,
        entitlement_receipt_id="rcpt_123",
    )

    assert cache_root() == user_cache
    assert str(project / ".proofsignal") not in str(entry.metadataPath)
    assert not (project / ".proofsignal").exists()
    loaded = load_cache_entry(platform="darwin-arm64")
    assert loaded is not None
    assert loaded.coreVersion == "0.12.0"

