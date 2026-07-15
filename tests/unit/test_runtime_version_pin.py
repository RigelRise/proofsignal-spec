from __future__ import annotations

from pathlib import Path

import pytest

from verifysignal_spec.runtime.models import REQUIRED_RUNTIME_BLOCKER_CODES
from verifysignal_spec.runtime.resolver import resolve_requested_core_version
from verifysignal_spec.workspace.repository import save_core_configuration


def test_env_pin_wins_over_workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    save_core_configuration(tmp_path, "verifysignal-core", version="0.4.0")
    monkeypatch.setenv("VERIFYSIGNAL_CORE_VERSION", "0.5.1")

    version, blocker = resolve_requested_core_version(tmp_path)

    assert version == "0.5.1"
    assert blocker is None


def test_workspace_version_used_when_env_unset(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("VERIFYSIGNAL_CORE_VERSION", raising=False)
    save_core_configuration(tmp_path, "verifysignal-core", version="0.5.1")

    version, blocker = resolve_requested_core_version(tmp_path)

    assert version == "0.5.1"
    assert blocker is None


def test_no_local_pin_yields_no_version_so_the_caller_asks_the_backend(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # This function answers ONE question: "is a version pinned locally?" — env, then workspace.
    # Returning None is not a dead-end verdict, it is the signal that makes the resolver ask the
    # backend for the current version (`/runtimes/latest`); see
    # tests/integration/test_first_run_version_resolution.py.
    #
    # The distinction is the whole bug. This test used to be named `test_blocker_when_no_version_is
    # _pinned` and read as if blocking were the correct PRODUCT behaviour. It was not: the persisted
    # version can only ever be written after a Core is installed, so on a fresh machine this function
    # cannot succeed by construction, and treating its None as final dead-ended every new user.
    monkeypatch.delenv("VERIFYSIGNAL_CORE_VERSION", raising=False)

    version, blocker = resolve_requested_core_version(tmp_path)

    assert version is None
    # The blocker is still well-formed for the case where the backend cannot answer either.
    assert blocker is not None
    assert blocker.code == "distribution.version-unspecified"
    assert blocker.recoveryCommand and "VERIFYSIGNAL_CORE_VERSION" in blocker.recoveryCommand
    assert blocker.code in REQUIRED_RUNTIME_BLOCKER_CODES
