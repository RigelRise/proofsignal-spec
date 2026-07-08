from __future__ import annotations

import json
import os

from helpers import CliTestCase


class ManagedRuntimeIntegrationReadinessTests(CliTestCase):
    def test_integration_install_reports_managed_runtime_readiness(self) -> None:
        code, out, err = self.cli(["integration", "install", "codex", "--project", str(self.project), "--json"])

        assert code == 0, err
        payload = json.loads(out)
        assert payload["managedRuntimeReadiness"]["status"] == "ready"
        assert payload["managedRuntimeReadiness"]["source"] == "env"

    def test_check_has_sub_second_structured_blocker_without_runtime(self) -> None:
        os.environ.pop("VERIFYSIGNAL_CORE_CMD", None)
        os.environ["VERIFYSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "empty-cache")
        self.addCleanup(lambda: os.environ.pop("VERIFYSIGNAL_RUNTIME_CACHE_DIR", None))

        code, out, _err = self.cli(["check", "--project", str(self.project), "--json"])

        assert code == 2
        payload = json.loads(out)
        assert payload["managedRuntimeReadiness"]["blockers"][0]["repairable"] is False

