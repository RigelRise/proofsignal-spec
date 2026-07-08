from __future__ import annotations

import json

from verifysignal_spec.runtime.models import ManagedRuntimeReadinessResult, RuntimeSetupBlocker, redact_runtime_payload


def test_runtime_result_redacts_secret_like_commands_and_messages() -> None:
    result = ManagedRuntimeReadinessResult(
        status="blocked",
        runtimeCommand="/tmp/verifysignal-core --token raw-email-token-123",
        blockers=[
            RuntimeSetupBlocker(
                code="entitlement.invalid-token",
                message="Token raw-email-token-123 was rejected.",
            )
        ],
    )

    payload = result.to_dict()
    text = json.dumps(payload)

    assert "raw-email-token-123" not in text
    assert payload["runtimeCommand"] == "[redacted]"
    assert payload["blockers"][0]["repairable"] is False


def test_redact_runtime_payload_covers_forbidden_categories() -> None:
    payload = redact_runtime_payload(
        {
            "token": "raw-token",
            "signedUrl": "https://example.invalid/file?signature=abc123",
            "screenshot": "base64-image",
            "browserStorage": {"localStorage": "secret"},
            "safe": "public runtime status",
        }
    )

    text = json.dumps(payload)
    assert "raw-token" not in text
    assert "abc123" not in text
    assert "base64-image" not in text
    assert "localStorage" not in text
    assert payload["safe"] == "public runtime status"

