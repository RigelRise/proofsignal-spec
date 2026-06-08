from __future__ import annotations

from helpers import FAKE_CORE
from tests.fixtures.workflows.skill_execution_boundary import ALIAS, create_planned_workspace, implementation_payload
from proofsignal_spec.workflows.stage_persistence import persist_stage
from tests.fixtures.workflows.workflow_dogfood_adjustments import minimal_specify_payload


def _workspace_text(project) -> str:
    root = project / ".proofsignal"
    if not root.exists():
        return ""
    return "\n".join(path.read_text(encoding="utf-8", errors="ignore") for path in root.rglob("*") if path.is_file())


def test_secret_target_locator_is_rejected_and_not_persisted_in_workflow_state(tmp_path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    secret_url = "https://qa-user:qa-password@example.com/app"

    result = persist_stage(project, "specify", alias="home-page-unauth", payload=minimal_specify_payload(target=secret_url))

    assert result["status"] == "invalid"
    assert "Secret-looking value" in result["blockers"][0]["message"]
    assert "qa-password" not in _workspace_text(project)


def test_tokenized_target_locator_is_rejected_and_not_persisted_in_run_artifacts(tmp_path) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    secret_url = "https://example.com/app?access_token=abc123abc123abc123"

    result = persist_stage(project, "specify", alias="home-page-unauth", payload=minimal_specify_payload(target=secret_url))

    assert result["status"] == "invalid"
    assert "Secret-looking value" in result["blockers"][0]["message"]
    assert "access_token" not in _workspace_text(project)


def test_composed_skill_preserves_credential_placeholders_without_persisting_env_values(tmp_path, monkeypatch) -> None:
    project = tmp_path / "repo"
    project.mkdir()
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("APP_TEST_EMAIL", "qa-user@example.com")
    monkeypatch.setenv("APP_TEST_PASSWORD", "super-secret-password-value")
    create_planned_workspace(project)

    result = persist_stage(project, "implement", alias=ALIAS, payload=implementation_payload(composed_main=False))

    workspace_text = _workspace_text(project)
    assert result["status"] == "persisted"
    assert "{{credentials.feats.email}}" in workspace_text
    assert "{{credentials.feats.password}}" in workspace_text
    assert "qa-user@example.com" not in workspace_text
    assert "super-secret-password-value" not in workspace_text
