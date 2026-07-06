from __future__ import annotations

import hashlib
from pathlib import Path

from proofsignal_spec.runtime.distribution import (
    manifest_entries,
    normalize_platform,
    select_manifest_entry,
    signature_contract_available,
    verify_sha256,
)


def test_normalize_platform_supports_documented_platforms() -> None:
    assert normalize_platform(system="Darwin", machine="arm64") == "darwin-arm64"
    assert normalize_platform(system="Darwin", machine="x86_64") == "darwin-x64"
    assert normalize_platform(system="Linux", machine="x86_64") == "linux-x64"
    assert normalize_platform(system="Windows", machine="AMD64") is None


def test_manifest_selection_requires_platform_contract_and_signature() -> None:
    manifest = {
        "entries": [
            {
                "coreVersion": "0.5.1",
                "contractVersion": "proofsignal-public-cli-json/v1",
                "platform": "darwin-arm64",
                "url": "file:///tmp/runtime.tar.gz",
                "sha256": "a" * 64,
                "signature": {"algorithm": "test", "keyId": "test", "value": "valid"},
            }
        ]
    }

    entries = manifest_entries(manifest)
    selected = select_manifest_entry(entries, platform="darwin-arm64", contract_version="proofsignal-public-cli-json/v1")

    assert selected["coreVersion"] == "0.5.1"
    assert signature_contract_available(selected)


def test_verify_sha256_detects_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.tar.gz"
    artifact.write_text("runtime", encoding="utf-8")

    assert verify_sha256(artifact, hashlib.sha256(b"runtime").hexdigest())
    assert not verify_sha256(artifact, "0" * 64)

