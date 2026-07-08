from __future__ import annotations

import os
from pathlib import Path

from helpers import FAKE_CORE
from tests.fixtures.managed_runtime import write_fake_core_executable

from verifysignal_spec.runtime.resolver import ensure_core_runtime
from verifysignal_spec.workspace.repository import init_workspace, save_core_configuration


def test_explicit_core_command_wins_before_managed_sources(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))

    result = ensure_core_runtime(tmp_path, explicit_core_cmd=str(FAKE_CORE))

    assert result.status == "ready"
    assert result.source == "explicit"
    assert result.runtimeCommand == str(FAKE_CORE)


def test_workspace_core_command_wins_over_environment(tmp_path: Path, monkeypatch) -> None:
    init_workspace(tmp_path)
    save_core_configuration(tmp_path, str(FAKE_CORE), source="workspace", version="0.1.0")
    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", "missing-env-core")

    result = ensure_core_runtime(tmp_path)

    assert result.status == "ready"
    assert result.source == "workspace"


def test_verifysignal_core_path_candidate_is_selected(tmp_path: Path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    core = write_fake_core_executable(bin_dir / "verifysignal-core")
    monkeypatch.delenv("VERIFYSIGNAL_CORE_CMD", raising=False)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))

    result = ensure_core_runtime(tmp_path)

    assert result.status == "ready"
    assert result.source == "path"
    assert result.runtimeCommand == str(core)


def test_public_verifysignal_path_candidate_is_not_selected_as_core(tmp_path: Path, monkeypatch) -> None:
    bin_dir = tmp_path / "bin"
    public_cli = write_fake_core_executable(bin_dir / "verifysignal")
    monkeypatch.delenv("VERIFYSIGNAL_CORE_CMD", raising=False)
    monkeypatch.setenv("PATH", f"{bin_dir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))

    result = ensure_core_runtime(tmp_path)

    assert result.runtimeCommand != str(public_cli)
    assert all(attempt.source != "path" or attempt.command != str(public_cli) for attempt in result.attempts)

