from __future__ import annotations

from proofsignal_spec.commands.repair import run as repair_run
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


def test_repair_with_missing_core_and_no_finding_is_environment_setup_noop(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", "missing-proofsignal-core-repair")
    create_main_skill_coverage_workspace(tmp_path)
    use_case_path = tmp_path / ".proofsignal/use-cases/profile-view-unauth.yaml"
    before = use_case_path.read_text(encoding="utf-8")

    result = repair_run(tmp_path, "profile-view-unauth")

    assert result["status"] == "blocked"
    assert result["findings"] == []
    assert result["applications"] == []
    assert result["rootCauseCategory"] == "environment-setup"
    assert result["nextCommand"] == "proofsignal-spec core setup --json"
    assert "Core setup is required" in result["message"]
    assert use_case_path.read_text(encoding="utf-8") == before
