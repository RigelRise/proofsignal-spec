from __future__ import annotations

from verifysignal_spec.workflows.engine import _apply_public_redaction_policy


def test_public_redaction_policy_uses_current_core_forbidden_field_shapes() -> None:
    core_contract = {
        "source": "core-public-contract",
        "runtimeIdentity": "/Users/example/private/verifysignal/apps/verifysignal-cli/dist/main.js",
        "runtimeCommand": "node /Users/example/private/verifysignal/apps/verifysignal-cli/dist/main.js",
        "sections": {
            "publicRedactionPolicy": {
                "publicErrorShape": {
                    "forbiddenFields": ["rawValue", "signedUrl", "absolutePath"],
                },
                "safeEvidenceReferences": {
                    "forbiddenFields": ["rawPayload", "signedUrl", "absolutePath"],
                },
            }
        },
        "diagnostics": {
            "rawValue": "secret-token-value",
            "signedUrl": "https://storage.example.test/evidence.png?X-Amz-Signature=private",
            "absolutePath": "/Users/example/private/evidence.png",
            "safeFieldPath": "publicRedactionPolicy.publicErrorShape.forbiddenFields",
        },
    }

    redacted = _apply_public_redaction_policy(core_contract)

    assert redacted["runtimeIdentity"] == "[redacted]"
    assert redacted["runtimeCommand"] == "[redacted]"
    assert redacted["diagnostics"]["rawValue"] == "[redacted]"
    assert redacted["diagnostics"]["signedUrl"] == "[redacted]"
    assert redacted["diagnostics"]["absolutePath"] == "[redacted]"
    assert redacted["diagnostics"]["safeFieldPath"] == "publicRedactionPolicy.publicErrorShape.forbiddenFields"
