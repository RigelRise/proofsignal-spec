from __future__ import annotations

import os
import time

from helpers import CliTestCase


class ManagedRuntimePerformanceTests(CliTestCase):
    def tearDown(self) -> None:
        os.environ.pop("VERIFYSIGNAL_RUNTIME_CACHE_DIR", None)
        super().tearDown()

    def test_blocker_classification_completes_quickly_without_runtime(self) -> None:
        os.environ.pop("VERIFYSIGNAL_CORE_CMD", None)
        os.environ["VERIFYSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "empty-cache")

        start = time.monotonic()
        code, _out, _err = self.cli(["check", "--project", str(self.project), "--json"])
        elapsed = time.monotonic() - start

        assert code == 2
        assert elapsed < 1

