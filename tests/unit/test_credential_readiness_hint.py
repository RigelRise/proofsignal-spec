from __future__ import annotations

from proofsignal_spec.workspace.models import CredentialReadinessHint
from proofsignal_spec.workspace.repository import load_credential_readiness_hint, save_credential_readiness_hint
from proofsignal_spec.workspace.validation import validate_credential_readiness_hint


def test_credential_readiness_hint_serializes_names_without_values(tmp_path) -> None:
    hint = CredentialReadinessHint(
        credentialGroup="feats",
        expectedSource="environment",
        requiredRuntimeNames=["APP_TEST_EMAIL", "APP_TEST_PASSWORD"],
        preparationHint="Load credentials with your approved local wrapper before running ProofSignal.",
    )

    save_credential_readiness_hint(tmp_path, hint)
    loaded = load_credential_readiness_hint(tmp_path, "feats")

    assert loaded
    assert loaded.valuesIncluded is False
    assert loaded.requiredRuntimeNames == ["APP_TEST_EMAIL", "APP_TEST_PASSWORD"]
    assert "approved local wrapper" in loaded.preparationHint


def test_credential_readiness_hint_rejects_secret_like_values() -> None:
    hint = CredentialReadinessHint(
        credentialGroup="feats",
        expectedSource="environment",
        requiredRuntimeNames=["APP_TEST_EMAIL"],
        preparationHint="APP_TEST_PASSWORD=super-secret-password-value",
    )

    findings = validate_credential_readiness_hint(hint)

    assert findings
    assert findings[0]["code"] == "credential-hint-secret-looking-value"
