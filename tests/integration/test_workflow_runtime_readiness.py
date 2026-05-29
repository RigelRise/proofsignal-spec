from __future__ import annotations

import json

from proofsignal_spec.commands.validate import run as validate_run
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


def test_unreachable_target_blocks_readiness_without_rewriting_artifacts(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_main_skill_coverage_workspace(tmp_path)
    run_request_path = tmp_path / ".proofsignal/run-requests/profile-view-unauth.yaml"
    run_request = json.loads(run_request_path.read_text(encoding="utf-8"))
    run_request["parameters"]["baseUrl"] = "https://"
    run_request_path.write_text(json.dumps(run_request), encoding="utf-8")

    result = validate_run(tmp_path, "profile-view-unauth", runtime_readiness=True, core_cmd=str(FAKE_CORE))

    assert result["status"] == "blocked"
    assert result["runtimeReadiness"]["targetReachabilityStatus"] == "unreachable"
    assert "runtime.target-unreachable" in result["runtimeReadiness"]["findingIds"]
    assert run_request_path.read_text(encoding="utf-8") == json.dumps(run_request)


def test_runtime_readiness_says_full_browser_flow_has_not_executed(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    create_main_skill_coverage_workspace(tmp_path)

    result = validate_run(tmp_path, "profile-view-unauth", runtime_readiness=True, core_cmd=str(FAKE_CORE))

    assert result["fullBrowserFlowExecuted"] is False
    assert result["runtimeReadiness"]["fullBrowserFlowExecuted"] is False
    assert "full browser flow has not executed" in result["readinessSummary"]
