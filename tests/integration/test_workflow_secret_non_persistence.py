from __future__ import annotations

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
