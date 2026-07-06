from __future__ import annotations

from pathlib import Path

import pytest

from proofsignal_spec.runtime.models import REQUIRED_RUNTIME_BLOCKER_CODES
from proofsignal_spec.runtime.resolver import resolve_requested_core_version
from proofsignal_spec.workspace.repository import save_core_configuration


def test_env_pin_wins_over_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    save_core_configuration(tmp_path, "proofsignal-core", version="0.4.0")
    monkeypatch.setenv("PROOFSIGNAL_CORE_VERSION", "0.5.1")

    version, blocker = resolve_requested_core_version(tmp_path)

    assert version == "0.5.1"
    assert blocker is None


def test_workspace_version_used_when_env_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROOFSIGNAL_CORE_VERSION", raising=False)
    save_core_configuration(tmp_path, "proofsignal-core", version="0.5.1")

    version, blocker = resolve_requested_core_version(tmp_path)

    assert version == "0.5.1"
    assert blocker is None


def test_blocker_when_no_version_is_pinned(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PROOFSIGNAL_CORE_VERSION", raising=False)

    version, blocker = resolve_requested_core_version(tmp_path)

    assert version is None
    assert blocker is not None
    assert blocker.code == "distribution.version-unspecified"
    assert blocker.recoveryCommand and "PROOFSIGNAL_CORE_VERSION" in blocker.recoveryCommand
    assert blocker.code in REQUIRED_RUNTIME_BLOCKER_CODES
