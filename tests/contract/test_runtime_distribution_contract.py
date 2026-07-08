from __future__ import annotations

from verifysignal_spec.runtime.distribution import manifest_entries, select_manifest_entry
from verifysignal_spec.runtime.models import REQUIRED_RUNTIME_BLOCKER_CODES


def test_runtime_manifest_entry_contract_selects_platform_and_contract() -> None:
    manifest = {
        "entries": [
            {
                "coreVersion": "0.5.1",
                "contractVersion": "verifysignal-public-cli-json/v1",
                "platform": "linux-x64",
                "artifactName": "verifysignal-core-linux-x64.tar.gz",
                "url": "file:///tmp/verifysignal-core-linux-x64.tar.gz",
                "sha256": "a" * 64,
                "signature": {"algorithm": "test", "keyId": "test", "value": "valid"},
            }
        ]
    }

    selected = select_manifest_entry(manifest_entries(manifest), platform="linux-x64")

    assert selected["coreVersion"] == "0.5.1"


def test_distribution_failure_codes_are_public_contract() -> None:
    assert {
        "credentials.unavailable",
        "manifest.unavailable",
        "manifest.invalid",
        "artifact.integrity-failed",
        "artifact.authenticity-failed",
        "distribution.unavailable",
    }.issubset(REQUIRED_RUNTIME_BLOCKER_CODES)

