from __future__ import annotations

import json
import contextlib
import io
import os
import stat
import sys
import time
from pathlib import Path

import pytest

from helpers import FAKE_CORE

from proofsignal_spec.workflows.core_setup import run_core_setup
from proofsignal_spec.workflows.readiness import core_readiness
from proofsignal_spec.workspace.repository import (
    get_core_configuration,
    init_workspace,
    load_document,
    save_core_configuration,
)


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
                f"os.environ['FAKE_PROOFSIGNAL_MODE'] = {mode!r}",
                f"sys.argv = [{str(FAKE_CORE)!r}, *sys.argv[1:]]",
                f"runpy.run_path({str(FAKE_CORE)!r}, run_name='__main__')",
                "",
            ]
        ),
    )


def _write_dev_core_dir(path: Path, *, mode: str = "ok") -> None:
    path.mkdir(parents=True)
    (path / "package.json").write_text(
        json.dumps({"scripts": {"proofsignal:dev": f"FAKE_PROOFSIGNAL_MODE={mode} {FAKE_CORE}"}}),
        encoding="utf-8",
    )


def test_workspace_core_configuration_metadata_is_persisted(tmp_path: Path) -> None:
    init_workspace(tmp_path)

    save_core_configuration(tmp_path, str(FAKE_CORE), source="env", version="0.1.0")

    workspace = load_document(tmp_path / ".proofsignal/workspace.yaml")
    assert workspace["coreCommand"] == str(FAKE_CORE)
    assert workspace["coreCommandSource"] == "env"
    assert workspace["coreConfiguredAt"].endswith("Z")
    assert workspace["coreLastVerifiedAt"].endswith("Z")
    assert workspace["coreVersion"] == "0.1.0"
    assert get_core_configuration(tmp_path)["coreCommand"] == str(FAKE_CORE)


def test_setup_from_environment_persists_and_later_readiness_reuses_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))

    setup = run_core_setup(tmp_path)

    assert setup.status == "ready"
    assert setup.source == "env"
    assert setup.persisted is True
    monkeypatch.delenv("PROOFSIGNAL_CORE_CMD", raising=False)
    readiness = core_readiness(tmp_path)
    assert readiness.status == "available"
    assert readiness.coreCommand == str(FAKE_CORE)


def test_explicit_one_time_override_does_not_persist(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))

    setup = run_core_setup(tmp_path, explicit_core_cmd=str(FAKE_CORE), persist=False)

    assert setup.status == "ready"
    assert setup.oneTime is True
    assert setup.persisted is False
    workspace = load_document(tmp_path / ".proofsignal/workspace.yaml")
    assert "coreCommand" not in workspace


def test_explicit_core_repo_directory_persists_resolved_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    core_repo = tmp_path / "proofsignal-core"
    _write_dev_core_dir(core_repo)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))

    setup = run_core_setup(tmp_path, explicit_core_cmd=str(core_repo))

    assert setup.status == "ready"
    assert setup.source == "explicit"
    assert setup.coreCommand != str(core_repo)
    assert "proofsignal:dev" in setup.coreCommand
    workspace = load_document(tmp_path / ".proofsignal/workspace.yaml")
    assert workspace["coreCommand"] == setup.coreCommand
    assert workspace["coreCommandSource"] == "explicit"


def test_workspace_candidate_takes_precedence_over_environment(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    save_core_configuration(tmp_path, str(FAKE_CORE), source="workspace", version="0.1.0")
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", "missing-env-core")

    setup = run_core_setup(tmp_path)

    assert setup.status == "ready"
    assert setup.source == "workspace"
    assert setup.attempts[0].source == "workspace"


def test_ancestor_sibling_discovery_persists_verified_command(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    parent = tmp_path / "parent"
    project = parent / "target"
    project.mkdir(parents=True)
    init_workspace(project)
    _write_dev_core_dir(parent / "proofsignal")
    monkeypatch.delenv("PROOFSIGNAL_CORE_CMD", raising=False)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))

    setup = run_core_setup(project)

    assert setup.status == "ready"
    assert setup.source == "ancestor-sibling"
    assert setup.coreCommand != str((parent / "proofsignal").resolve())
    assert "proofsignal:dev" in setup.coreCommand
    workspace = load_document(project / ".proofsignal/workspace.yaml")
    assert workspace["coreCommand"] == setup.coreCommand
    assert workspace["coreCommandSource"] == "ancestor-sibling"


def test_setup_missing_scenario_completes_under_five_seconds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    init_workspace(tmp_path)
    monkeypatch.delenv("PROOFSIGNAL_CORE_CMD", raising=False)
    monkeypatch.setenv("PATH", "")

    start = time.monotonic()
    setup = run_core_setup(tmp_path)
    elapsed = time.monotonic() - start

    assert setup.status == "missing"
    assert elapsed < 5


def test_core_setup_cli_json_ready_and_text_ready(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))

    code, out, err = _cli(["core", "setup", "--project", str(tmp_path), "--json"])

    assert code == 0, err
    payload = json.loads(out)
    assert payload["status"] == "ready"
    assert payload["source"] == "env"

    code, out, err = _cli(["core", "setup", "--project", str(tmp_path)])
    assert code == 0, err
    assert "ProofSignal Core setup" in out
    assert "Status: [READY]" in out
    assert "Source:" in out
    assert "Command:" in out


def test_core_setup_cli_text_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", "missing-proofsignal-core-cli")

    code, out, err = _cli(["core", "setup", "--project", str(tmp_path)])

    assert code == 0, err
    assert "Status: [BLOCKED]" in out
    assert "ProofSignal Core was not found." in out
    assert "Next: proofsignal core setup --json" in out


def test_core_setup_cli_ready_scenario_completes_under_five_seconds(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_CORE_CMD", str(FAKE_CORE))

    start = time.monotonic()
    code, out, err = _cli(["core", "setup", "--project", str(tmp_path), "--json"])
    elapsed = time.monotonic() - start

    assert code == 0, err
    assert json.loads(out)["status"] == "ready"
    assert elapsed < 5


def _cli(args: list[str]) -> tuple[int, str, str]:
    from proofsignal_spec.cli import main

    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        code = main(args)
    return code, stdout.getvalue(), stderr.getvalue()
