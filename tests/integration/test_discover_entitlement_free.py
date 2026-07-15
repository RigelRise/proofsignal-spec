from __future__ import annotations

from pathlib import Path

import pytest

from tests.fixtures.managed_runtime import write_fake_core_executable
from verifysignal_spec.runtime.cache import save_cache_entry
from verifysignal_spec.runtime.distribution import normalize_platform
from verifysignal_spec.runtime.resolver import ensure_core_runtime


def _cache_a_core(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, mode: str) -> str:
    """Cache a managed Core (running the fake in `mode`) and route the resolver to the managed path
    by removing every override source (env/workspace/PATH)."""
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_CORE_CMD", raising=False)
    platform = normalize_platform()
    assert platform is not None
    core = write_fake_core_executable(tmp_path / "bin" / "verifysignal-core", mode=mode)
    save_cache_entry(core_version="0.5.1", platform=platform, runtime_command=str(core))
    return platform


def test_discover_resolves_entitlement_free_when_cached_core_advertises_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # No receipt, managed path, cached Core advertises verifysignal.discover/v1 -> discover must
    # resolve entitlement-free. (Before the fix the managed path called ensure_entitlement first and
    # blocked with entitlement.unlock-required.)
    _cache_a_core(tmp_path, monkeypatch, mode="advertises-discover")

    result = ensure_core_runtime(tmp_path, context="discover")

    assert result.status == "ready"
    assert result.entitlement.status == "not-required"


def test_protected_context_still_requires_entitlement_with_the_same_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Security scope: the entitlement-free branch is discover-ONLY. A protected context must still
    # block without a receipt even though the very same discover-capable Core is cached.
    _cache_a_core(tmp_path, monkeypatch, mode="advertises-discover")

    result = ensure_core_runtime(tmp_path, context="runtime")

    assert result.status == "blocked"


def test_discover_blocks_on_the_override_path_when_core_lacks_the_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Capability negotiation must cover EVERY source, not just the managed-cache branch. An explicit
    # override (VERIFYSIGNAL_CORE_CMD / workspace / PATH) pointing at a compatible Core that does NOT
    # advertise verifysignal.discover/v1 used to resolve `ready` and then blow up inside Core on the
    # unknown `discover` subcommand. Fail early with a clear capability blocker instead.
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    core = write_fake_core_executable(tmp_path / "bin" / "verifysignal-core", mode="ok")
    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(core))

    result = ensure_core_runtime(tmp_path, context="discover")

    assert result.status == "blocked"
    assert any(blocker.code == "core.discover-unsupported" for blocker in result.blockers)


def test_override_still_resolves_for_protected_contexts_without_the_discover_capability(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Scope guard: a capability is required only by the contexts that INVOKE it (see
    # CONTEXT_REQUIRED_CAPABILITY). The same non-discover Core must still resolve normally for a
    # context that does not need discover — it is a perfectly valid Core for running.
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    core = write_fake_core_executable(tmp_path / "bin" / "verifysignal-core", mode="ok")
    monkeypatch.setenv("VERIFYSIGNAL_CORE_CMD", str(core))

    result = ensure_core_runtime(tmp_path, context="runtime")

    assert result.status == "ready"


def test_discover_still_blocks_when_cached_core_does_not_advertise_discover(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Capability gate: a cached Core that does NOT advertise discover gets no free pass — discover
    # falls through to the entitlement gate and blocks without a receipt.
    _cache_a_core(tmp_path, monkeypatch, mode="ok")

    result = ensure_core_runtime(tmp_path, context="discover")

    assert result.status == "blocked"
