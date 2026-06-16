from __future__ import annotations

from proofsignal_spec.commands.validate import run as validate_run
from proofsignal_spec.workspace.models import CredentialReadinessHint
from proofsignal_spec.workspace.repository import save_credential_readiness_hint
from tests.fixtures.workflows.live_write_readiness import create_live_write_readiness_workspace


def test_runtime_readiness_surfaces_credential_hint_without_reading_secret_file(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.delenv("APP_TEST_EMAIL", raising=False)
    monkeypatch.delenv("APP_TEST_PASSWORD", raising=False)
    create_live_write_readiness_workspace(tmp_path)
    save_credential_readiness_hint(
        tmp_path,
        CredentialReadinessHint(
            credentialGroup="feats",
            expectedSource="environment",
            requiredRuntimeNames=["APP_TEST_EMAIL", "APP_TEST_PASSWORD"],
            preparationHint="Use the team-approved secret wrapper before validation.",
        ),
    )

    result = validate_run(tmp_path, "brands-search-authenticated", runtime_readiness=True, core_cmd=str(FAKE_CORE))

    assert result["status"] == "blocked"
    readiness = result["runtimeReadiness"]["credentialReadiness"][0]
    assert readiness["missingRuntimeNames"] == ["APP_TEST_EMAIL", "APP_TEST_PASSWORD"]
    assert readiness["valuesIncluded"] is False
    assert "team-approved secret wrapper" in readiness["preparationHint"]
