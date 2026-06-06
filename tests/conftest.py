from __future__ import annotations

import os

import pytest


@pytest.fixture(autouse=True)
def isolate_proofsignal_runtime_cache(tmp_path, monkeypatch):
    if "PROOFSIGNAL_RUNTIME_CACHE_DIR" not in os.environ:
        monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "runtime-cache"))
