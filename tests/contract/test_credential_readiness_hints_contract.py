from __future__ import annotations

from proofsignal_spec.workflows.runtime_readiness import evaluate_runtime_readiness
from proofsignal_spec.workspace.models import CredentialReadinessHint
from proofsignal_spec.workspace.repository import save_credential_readiness_hint
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_missing_credential_blocker_includes_group_names_runtime_names_and_hint(tmp_path, monkeypatch) -> None:
    create_live_write_readiness_workspace(tmp_path)
    save_credential_readiness_hint(
        tmp_path,
        CredentialReadinessHint(
            credentialGroup="feats",
            expectedSource="environment",
            requiredRuntimeNames=["APP_TEST_EMAIL", "APP_TEST_PASSWORD"],
            preparationHint="Use your chosen secret manager wrapper before validation.",
        ),
    )
    monkeypatch.delenv("APP_TEST_EMAIL", raising=False)
    monkeypatch.delenv("APP_TEST_PASSWORD", raising=False)

    result = evaluate_runtime_readiness(tmp_path, "brands-search-authenticated").to_dict()

    assert result["status"] == "blocked"
    assert "runtime.credential-missing.feats" in result["findingIds"]
    assert result["credentialReadiness"][0]["credentialGroup"] == "feats"
    assert result["credentialReadiness"][0]["requiredRuntimeNames"] == ["APP_TEST_EMAIL", "APP_TEST_PASSWORD"]
    assert result["credentialReadiness"][0]["valuesIncluded"] is False
    assert "secret manager wrapper" in result["credentialReadiness"][0]["preparationHint"]
