"""Cross-repo interop ratchet (Fix 4d).

This golden file is byte-for-byte identical to the copies committed in Core and BE — a single
Core-signed release-metadata blob. Spec must verify it with the SAME committed TEST key, accept it
through ``verify_release_authenticity`` (signature + sha + contract + coreVersion bindings), reject a
coreVersion tamper, and accept the trusted key in base64-DER form too. A divergence in any repo
(dropping the coreVersion binding, or refusing a documented key format) fails CI in that repo.
"""

from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any

import pytest

from verifysignal_spec.runtime.distribution import verify_release_authenticity
from verifysignal_spec.runtime.release_signature import (
    TEST_RELEASE_KEY_ID,
    verify_release_signature,
)

_GOLDEN = json.loads(
    (Path(__file__).resolve().parents[1] / "fixtures" / "cross_repo_release_golden.json").read_text("utf-8")
)

# SPKI base64-DER form of the committed TEST release public key (identical across all three repos).
TEST_RELEASE_PUBLIC_KEY_DER = "MCowBQYDK2VwAyEA9cu+k/slRJsVRXV7mGPjJYtsqNO6DFFUi8phMq3Hiqw="


def _golden_entry(**overrides: Any) -> dict[str, Any]:
    entry: dict[str, Any] = {
        "coreVersion": _GOLDEN["expected"]["coreVersion"],
        "contractVersion": _GOLDEN["expected"]["publicContractVersion"],
        "platform": _GOLDEN["expected"]["platform"],
        "url": "file:///tmp/verifysignal-core.tar.gz",
        "sha256": _GOLDEN["expected"]["sha256"],
        "releaseMetadataBytes": _GOLDEN["releaseMetadataBytes"],
        "signature": _GOLDEN["signature"],
    }
    entry.update(overrides)
    return entry


def test_golden_accepts_and_binds_core_version(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS", "1")

    metadata_bytes = base64.b64decode(_GOLDEN["releaseMetadataBytes"])
    ok, key_id = verify_release_signature(metadata_bytes, _GOLDEN["signature"])
    assert ok is True and key_id == TEST_RELEASE_KEY_ID

    # Full authenticity path accepts the Core-signed golden (sha + contract + coreVersion all bind).
    assert verify_release_authenticity(_golden_entry()) is None

    # Re-point the entry's coreVersion at a value the signature does not cover -> fail closed.
    blocker = verify_release_authenticity(_golden_entry(coreVersion="9.9.9"))
    assert blocker is not None and blocker.code == "artifact.authenticity-failed"


def test_golden_verifies_with_base64_der_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS", raising=False)
    monkeypatch.setenv(
        "VERIFYSIGNAL_RUNTIME_RELEASE_PUBLIC_KEYS",
        json.dumps({TEST_RELEASE_KEY_ID: TEST_RELEASE_PUBLIC_KEY_DER}),
    )

    metadata_bytes = base64.b64decode(_GOLDEN["releaseMetadataBytes"])
    ok, key_id = verify_release_signature(metadata_bytes, _GOLDEN["signature"])
    assert ok is True and key_id == TEST_RELEASE_KEY_ID
