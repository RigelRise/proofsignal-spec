"""Shared helper for signing runtime-release metadata with the TEST release key.

Core signs a detached Ed25519 signature over the EXACT release-metadata file bytes; the
managed installer verifies that signature against a trusted release key before trusting an
archive. Tests that exercise the install/select path need a genuinely signed entry, not a
self-reported stub. This helper produces one with the committed TEST key (trusted only when
``VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS == "1"``), which we set here for the test process.
"""

from __future__ import annotations

import base64
import json
import os
from typing import Any

from cryptography.hazmat.primitives.serialization import load_pem_private_key

os.environ.setdefault("VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS", "1")

TEST_RELEASE_KEY_ID = "verifysignal-core-release-test-key"
TEST_RELEASE_PRIVATE_KEY_PEM = """-----BEGIN PRIVATE KEY-----
MC4CAQAwBQYDK2VwBCIEIHo4Do7CxUHugcTuwe6Jwiz1D8K8sBJ2GJ6HCnK059+d
-----END PRIVATE KEY-----
"""


def sign_release_metadata(metadata: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Sign ``metadata`` and return ``(releaseMetadataBytes_b64, signature_block)``.

    The signature covers the exact JSON bytes returned here; callers must attach both the
    returned base64 bytes and signature block to the entry unchanged (a re-serialize would
    break the byte-exact signature).
    """
    metadata_bytes = json.dumps(metadata).encode("utf-8")
    private_key = load_pem_private_key(TEST_RELEASE_PRIVATE_KEY_PEM.encode("utf-8"), password=None)
    signature_value = base64.b64encode(private_key.sign(metadata_bytes)).decode("ascii")
    signature_block = {
        "schema": "verifysignal.runtime-signature/v1",
        "schemaVersion": 1,
        "algorithm": "ed25519",
        "keyId": TEST_RELEASE_KEY_ID,
        "signature": signature_value,
    }
    return base64.b64encode(metadata_bytes).decode("ascii"), signature_block


def signed_manifest_entry(
    *,
    platform: str,
    sha256: str,
    contract: str = "verifysignal-public-cli-json/v1",
    signed_sha256: str | None = None,
    core_version: str = "0.5.1",
    signed_core_version: str | None = None,
    signed_filename: str | None = None,
    signed_schema: str = "verifysignal.runtime-release/v1",
    channel: str = "stable",
    issuer: str = "https://verifysignal.io",
    **overrides: Any,
) -> dict[str, Any]:
    """Build a manifest entry with a real detached signature over its release metadata.

    ``signed_sha256`` defaults to ``sha256``; pass a different value to simulate an archive
    whose checksum does not match the signed metadata (authenticity must fail closed).
    ``signed_core_version`` defaults to the entry's (possibly overridden) ``coreVersion``; pass a
    different value to simulate an entry re-pointed at a coreVersion the signature does not cover.
    ``signed_filename`` defaults to the entry's ``artifactName``, and ``signed_schema`` to the real
    release schema; both can be forced to simulate a signature that does not cover the entry's
    claimed filename, or a foreign document signed by a trusted key.
    """
    entry: dict[str, Any] = {
        "coreVersion": core_version,
        "contractVersion": contract,
        "platform": platform,
        "url": "file:///tmp/verifysignal-core.tar.gz",
        "sha256": sha256,
    }
    entry.update(overrides)
    # Core signs coreVersion into the release metadata; bind the SIGNED coreVersion to the entry's
    # final coreVersion by default so real installs verify, while signed_sha256/signed_core_version
    # let a test force a signature that does not cover the entry's claimed sha/version.
    #
    # `filename` mirrors what Core ACTUALLY signs — see tests/fixtures/cross_repo_release_golden.json,
    # whose real signed packages[] entry carries it. The fixture omitted it, which is part of why the
    # installer never binding it went unnoticed.
    package: dict[str, Any] = {"platform": platform, "sha256": signed_sha256 or sha256}
    filename = signed_filename or entry.get("artifactName")
    if filename:
        package["filename"] = filename
    metadata = {
        "schema": signed_schema,
        "coreVersion": signed_core_version or entry["coreVersion"],
        "publicContractVersion": contract,
        "channel": channel,
        "issuer": issuer,
        "packages": [package],
    }
    metadata_b64, signature_block = sign_release_metadata(metadata)
    entry["releaseMetadataBytes"] = metadata_b64
    entry["signature"] = signature_block
    return entry
