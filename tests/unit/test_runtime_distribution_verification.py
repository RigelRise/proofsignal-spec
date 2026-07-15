from __future__ import annotations

import base64
import hashlib
from pathlib import Path

from verifysignal_spec.runtime.distribution import (
    manifest_entries,
    normalize_platform,
    select_manifest_entry,
    signature_contract_available,
    verify_release_authenticity,
    verify_sha256,
)

from tests.fixtures.release_signing import sign_release_metadata, signed_manifest_entry


def _entry_with_signed_metadata(metadata: dict, *, sha256: str, platform: str = "darwin-arm64") -> dict:
    """Build an entry around genuinely-signed `metadata` so the Ed25519 signature verifies and
    only the downstream cross-checks (sha / publicContractVersion) are under test."""
    metadata_b64, signature = sign_release_metadata(metadata)
    return {
        "coreVersion": "0.5.1",
        "contractVersion": "verifysignal-public-cli-json/v1",
        "platform": platform,
        "url": "file:///tmp/verifysignal-core.tar.gz",
        "sha256": sha256,
        "releaseMetadataBytes": metadata_b64,
        "signature": signature,
    }


def test_normalize_platform_supports_documented_platforms() -> None:
    assert normalize_platform(system="Darwin", machine="arm64") == "darwin-arm64"
    assert normalize_platform(system="Darwin", machine="x86_64") == "darwin-x64"
    assert normalize_platform(system="Linux", machine="x86_64") == "linux-x64"
    assert normalize_platform(system="Windows", machine="AMD64") is None


def test_manifest_selection_requires_a_real_signature_and_bytes() -> None:
    entry = signed_manifest_entry(platform="darwin-arm64", sha256="a" * 64)
    selected = select_manifest_entry(
        manifest_entries({"entries": [entry]}),
        platform="darwin-arm64",
        contract_version="verifysignal-public-cli-json/v1",
    )
    assert selected["coreVersion"] == "0.5.1"
    assert signature_contract_available(selected)

    # A self-reported stub (no detached signature / no signed bytes) is no longer selectable.
    stub = {**entry, "signature": {"algorithm": "test", "keyId": "test", "value": "valid"}}
    stub.pop("releaseMetadataBytes")
    assert not signature_contract_available(stub)


def test_verify_release_authenticity_accepts_valid_and_fails_closed() -> None:
    assert verify_release_authenticity(signed_manifest_entry(platform="darwin-arm64", sha256="a" * 64)) is None

    untrusted = signed_manifest_entry(platform="darwin-arm64", sha256="a" * 64)
    untrusted["signature"]["keyId"] = "unknown-release-key"
    blocker = verify_release_authenticity(untrusted)
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"

    tampered = signed_manifest_entry(platform="darwin-arm64", sha256="a" * 64)
    tampered["releaseMetadataBytes"] = base64.b64encode(b'{"tampered":true}').decode("ascii")
    blocker = verify_release_authenticity(tampered)
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"

    # Archive sha256 does not match the SIGNED sha256 (bytes still verify, cross-check fails).
    mismatch = signed_manifest_entry(platform="darwin-arm64", sha256="b" * 64, signed_sha256="a" * 64)
    blocker = verify_release_authenticity(mismatch)
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"

    no_bytes = signed_manifest_entry(platform="darwin-arm64", sha256="a" * 64)
    no_bytes["releaseMetadataBytes"] = None
    blocker = verify_release_authenticity(no_bytes)
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"


def test_verify_release_authenticity_requires_a_signed_public_contract_version() -> None:
    # Signed metadata that OMITS publicContractVersion must fail closed rather than silently
    # skipping the contract-version binding (L1 hardening).
    metadata = {
        "schema": "verifysignal.runtime-release/v1",
        "channel": "stable",
        "issuer": "https://verifysignal.io",
        "packages": [{"platform": "darwin-arm64", "sha256": "a" * 64}],
    }
    blocker = verify_release_authenticity(_entry_with_signed_metadata(metadata, sha256="a" * 64))
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"


def test_verify_release_authenticity_binds_core_version() -> None:
    # A validly-signed release re-pointed at a coreVersion the signature does not cover must fail
    # closed. coreVersion drives the cache path and the persisted install record, so a forged
    # coreVersion on an otherwise-authentic entry cannot be trusted.
    mismatch = signed_manifest_entry(
        platform="darwin-arm64", sha256="a" * 64, core_version="9.9.9", signed_core_version="0.5.1"
    )
    blocker = verify_release_authenticity(mismatch)
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"

    # Signed metadata that OMITS coreVersion must also fail closed (no silent skip), matching the
    # sha256 and publicContractVersion bindings.
    metadata = {
        "schema": "verifysignal.runtime-release/v1",
        "publicContractVersion": "verifysignal-public-cli-json/v1",
        "channel": "stable",
        "issuer": "https://verifysignal.io",
        "packages": [{"platform": "darwin-arm64", "sha256": "a" * 64}],
    }
    blocker = verify_release_authenticity(_entry_with_signed_metadata(metadata, sha256="a" * 64))
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"


def test_verify_release_authenticity_rejects_degenerate_sha_on_both_sides() -> None:
    # A signed package whose sha256 is empty / whitespace / non-hex must not authenticate an
    # entry with the same degenerate value via a bare equality ("" == "", "   " == "   ",
    # None -> "none" == "none"). Only a real 64-hex match may pass (L2 hardening).
    for degenerate in ("", "   ", None, "not-a-hash"):
        metadata = {
            "schema": "verifysignal.runtime-release/v1",
            "publicContractVersion": "verifysignal-public-cli-json/v1",
            "channel": "stable",
            "issuer": "https://verifysignal.io",
            "packages": [{"platform": "darwin-arm64", "sha256": degenerate}],
        }
        entry = _entry_with_signed_metadata(metadata, sha256="")
        entry["sha256"] = degenerate  # type: ignore[assignment]
        blocker = verify_release_authenticity(entry)
        assert blocker is not None and blocker.code == "artifact.authenticity-failed", degenerate


def test_verify_sha256_detects_mismatch(tmp_path: Path) -> None:
    artifact = tmp_path / "artifact.tar.gz"
    artifact.write_text("runtime", encoding="utf-8")
    assert verify_sha256(artifact, hashlib.sha256(b"runtime").hexdigest())
    assert not verify_sha256(artifact, "0" * 64)
