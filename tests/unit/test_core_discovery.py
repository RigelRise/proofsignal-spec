from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

import pytest

from helpers import FAKE_CORE

from verifysignal_spec.workspace.repository import init_workspace, load_document
from verifysignal_spec.workflows.core_setup import discover_candidates, run_core_setup, verify_candidate
from verifysignal_spec.workflows.models import CORE_SETUP_SCHEMA, CoreCandidateAttempt, CoreSetupResult


def _write_executable(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def _write_fake_core_script(path: Path, *, mode: str = "ok") -> None:
    _write_executable(
        path,
        "\n".join(
            [
                f"#!{sys.executable}",
                "import os, runpy, sys",
                f"os.environ['FAKE_VERIFYSIGNAL_MODE'] = {mode!r}",
                f"sys.argv = [{str(FAKE_CORE)!r}, *sys.argv[1:]]",
                f"runpy.run_path({str(FAKE_CORE)!r}, run_name='__main__')",
                "",
            ]
        ),
    )


def _write_dev_core_dir(path: Path, *, mode: str = "ok") -> None:
    path.mkdir(parents=True)
    (path / "package.json").write_text(
        json.dumps(
            {
                "scripts": {
                    "verifysignal:dev": f"FAKE_VERIFYSIGNAL_MODE={mode} {FAKE_CORE}",
                }
            }
        ),
        encoding="utf-8",
    )


def test_core_setup_result_serializes_contract_fields() -> None:
    attempt = CoreCandidateAttempt(
        source="env",
        command=str(FAKE_CORE),
        status="compatible",
        terminal=True,
        version="0.1.0",
        message="Core command verified through public CLI contract.",
    )
    result = CoreSetupResult(
        status="ready",
        coreCommand=str(FAKE_CORE),
        source="env",
        selectedCandidate=attempt,
        persisted=True,
        version="0.1.0",
        attempts=[attempt],
    )

    payload = result.to_dict()

    assert payload["schemaVersion"] == CORE_SETUP_SCHEMA
    assert payload["status"] == "ready"
    assert payload["selectedCandidate"]["source"] == "env"
    assert payload["selectedCandidate"]["status"] == "compatible"
    assert payload["requiredOperationsByName"]["report.inspect"]["schemaName"] == "verifysignal.report-inspection/v1"
    assert payload["missingOperations"] == []
    assert payload["incompatibleOperations"] == []


def test_verify_candidate_uses_core_adapter_and_directory_command_behavior(tmp_path: Path) -> None:
    core_repo = tmp_path / "verifysignal"
    _write_dev_core_dir(core_repo)

    attempt, compatibility = verify_candidate(tmp_path, source="ancestor-sibling", command=str(core_repo))

    assert attempt.status == "compatible"
    assert attempt.source == "ancestor-sibling"
    assert attempt.displayPath == str(core_repo.resolve())
    assert compatibility is not None
    assert compatibility.compatible is True


def test_discovery_prefers_explicit_before_workspace_env_path_and_local_dev(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path, core_cmd="workspace-verifysignal")
    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", "env-verifysignal")
    path_bin = tmp_path / "bin"
    path_bin.mkdir()
    _write_fake_core_script(path_bin / "verifysignal")
    monkeypatch.setenv("PATH", f"{path_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    candidates = discover_candidates(tmp_path, explicit_core_cmd=str(FAKE_CORE))

    assert [item.source for item in candidates[:4]] == ["explicit", "workspace", "env", "path"]
    assert candidates[0].command == str(FAKE_CORE)


def test_path_candidate_can_be_selected_and_persisted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    path_bin = tmp_path / "bin"
    path_bin.mkdir()
    core_path = path_bin / "verifysignal"
    _write_fake_core_script(core_path)
    monkeypatch.delenv("VERIFYSIGNAL_CORE_CMD", raising=False)
    monkeypatch.setenv("PATH", f"{path_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    result = run_core_setup(tmp_path)

    assert result.status == "ready"
    assert result.source == "path"
    assert result.coreCommand == str(core_path)
    assert result.persisted is True
    workspace = load_document(tmp_path / ".verifysignal/workspace.yaml")
    assert workspace["coreCommand"] == str(core_path)
    assert workspace["coreCommandSource"] == "path"
    assert workspace["coreVersion"] == "0.1.0"


def test_explicit_incompatible_candidate_is_terminal(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    path_bin = tmp_path / "bin"
    path_bin.mkdir()
    _write_fake_core_script(path_bin / "verifysignal", mode="ok")
    bad_core = tmp_path / "bad-core"
    _write_fake_core_script(bad_core, mode="incompatible-run-schema")
    monkeypatch.setenv("PATH", f"{path_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    result = run_core_setup(tmp_path, explicit_core_cmd=str(bad_core))

    assert result.status == "incompatible"
    assert result.source == "explicit"
    assert result.selectedCandidate is None
    assert result.attempts[0].status == "incompatible"
    assert result.attempts[0].terminal is True
    assert len(result.attempts) == 1


def test_path_incompatible_candidate_continues_to_ancestor_sibling(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = tmp_path / "workspace"
    project = parent / "target"
    project.mkdir(parents=True)
    init_workspace(project)
    path_bin = tmp_path / "bin"
    path_bin.mkdir()
    _write_fake_core_script(path_bin / "verifysignal", mode="incompatible-run-schema")
    _write_dev_core_dir(parent / "verifysignal", mode="ok")
    monkeypatch.delenv("VERIFYSIGNAL_CORE_CMD", raising=False)
    monkeypatch.setenv("PATH", f"{path_bin}{os.pathsep}{os.environ.get('PATH', '')}")

    result = run_core_setup(project)

    assert result.status == "ready"
    assert result.source == "ancestor-sibling"
    assert [attempt.status for attempt in result.attempts[:2]] == ["incompatible", "compatible"]
    assert result.attempts[0].terminal is False
    assert result.attempts[1].terminal is True
