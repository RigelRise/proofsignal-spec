from __future__ import annotations

import json
import contextlib
import io
import os
import shutil

from proofsignal_spec.commands.validate import run as validate_run
from proofsignal_spec.workflows.core_setup import run_core_setup
from proofsignal_spec.workflows.readiness import validation_readiness
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


def test_validate_missing_core_blocker_routes_to_setup(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", "missing-proofsignal-core-runtime")
    create_main_skill_coverage_workspace(tmp_path)

    result = validate_run(tmp_path, "profile-view-unauth", runtime_readiness=True)

    blocker = next(item for item in result["blockers"] if item["code"] == "core.missing")
    assert result["status"] == "blocked"
    assert blocker["category"] == "environment"
    assert blocker["repairable"] is False
    assert blocker["recoveryCommand"] == "proofsignal core setup --json"


def test_core_setup_success_clears_previous_missing_core_readiness(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    create_main_skill_coverage_workspace(tmp_path)
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", "missing-proofsignal-core-runtime")

    missing = validation_readiness(tmp_path, alias="profile-view-unauth")
    assert any(item["code"] == "core.missing" for item in missing["blockers"])

    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    setup = run_core_setup(tmp_path)
    assert setup.status == "ready"
    monkeypatch.delenv("PROOFSIGNAL_CORE_CMD", raising=False)

    ready = validation_readiness(tmp_path, alias="profile-view-unauth")
    assert ready["coreReadiness"]["status"] == "available"
    assert not any(item["code"] == "core.missing" for item in ready["blockers"])


def test_validation_readiness_uses_managed_runtime_discovery_not_spec_cli_on_path(tmp_path, monkeypatch) -> None:
    from tests.helpers import FAKE_CORE

    workspace_root = tmp_path / "workspace"
    project = workspace_root / "Feats" / "fe-feats"
    project.mkdir(parents=True)
    create_main_skill_coverage_workspace(project)
    shutil.copy2(FAKE_CORE, workspace_root / "proofsignal")
    os.chmod(workspace_root / "proofsignal", 0o755)

    spec_cli_bin = tmp_path / "spec-cli-bin"
    spec_cli_bin.mkdir()
    spec_cli = spec_cli_bin / "proofsignal"
    spec_cli.write_text(
        "#!/usr/bin/env sh\n"
        "echo \"proofsignal: error: argument command: invalid choice: 'version'\" >&2\n"
        "exit 2\n",
        encoding="utf-8",
    )
    os.chmod(spec_cli, 0o755)
    monkeypatch.delenv("PROOFSIGNAL_CORE_CMD", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_EMAIL", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT", raising=False)
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON", raising=False)
    monkeypatch.delenv("FAKE_PROOFSIGNAL_MODE", raising=False)
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "runtime-cache"))
    monkeypatch.setenv("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH", str(tmp_path / "runtime-cache" / "missing-receipt.json"))
    monkeypatch.setenv("PATH", str(spec_cli_bin) + os.pathsep + os.environ.get("PATH", ""))

    result = validation_readiness(project, alias="profile-view-unauth")

    assert result["status"] == "ready"
    assert result["coreReadiness"]["status"] == "available"
    assert result["coreReadiness"]["coreCommand"] == str(workspace_root / "proofsignal")
    assert not result["blockers"]


def test_run_missing_core_stderr_points_to_setup(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", "missing-proofsignal-core-run")
    create_main_skill_coverage_workspace(tmp_path)

    code, _out, err = _cli([
        "run",
        "profile-view-unauth",
        "--project",
        str(tmp_path),
        "--json",
        "--non-interactive",
    ])

    assert code == 3
    assert "proofsignal core setup --json" in err


def _cli(args: list[str]) -> tuple[int, str, str]:
    from proofsignal_spec.cli import main

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()
