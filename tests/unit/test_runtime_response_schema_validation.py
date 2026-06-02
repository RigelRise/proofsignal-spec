from __future__ import annotations

from proofsignal_spec.runtime.distribution import validate_runtime_authorization_response


def test_runtime_authorization_schema_validation_blocks_invalid_or_expired_grants() -> None:
    invalid = validate_runtime_authorization_response({"schema": "wrong"}, expected_platform="darwin-arm64")
    assert invalid and invalid.code == "manifest.invalid"

    expired = validate_runtime_authorization_response(
        {
            "schema": "proofsignal.runtime-download/v1",
            "schemaVersion": 1,
            "coreVersion": "0.12.0",
            "platform": "darwin-arm64",
            "package": {
                "filename": "proofsignal-core.tar.gz",
                "byteSize": 1,
                "sha256": "a" * 64,
                "downloadUrl": "https://example.invalid/runtime?signature=secret",
                "expiresAt": "2000-01-01T00:00:00Z",
            },
        },
        expected_platform="darwin-arm64",
    )
    assert expired and expired.code == "distribution.url-expired"

