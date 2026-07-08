from __future__ import annotations

import json
import os

from helpers import CliTestCase


class ManagedRuntimeReadinessTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ.pop("VERIFYSIGNAL_CORE_CMD", None)
        os.environ["VERIFYSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "user-cache")

    def tearDown(self) -> None:
        os.environ.pop("VERIFYSIGNAL_RUNTIME_CACHE_DIR", None)
        super().tearDown()

    def test_check_returns_structured_runtime_setup_blocker_when_runtime_missing(self) -> None:
        code, _out, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        assert code == 2, err

        code, out, _err = self.cli(["check", "--project", str(self.project), "--json"])
        payload = json.loads(out)

        assert code == 2
        assert payload["managedRuntimeReadiness"]["status"] == "blocked"
        assert payload["managedRuntimeReadiness"]["blockers"][0]["repairable"] is False

