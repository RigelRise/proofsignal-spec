from __future__ import annotations

import json
import os

from helpers import CliTestCase
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


class ManagedRuntimeRepairTests(CliTestCase):
    def test_repair_runtime_setup_blocker_does_not_edit_artifacts(self) -> None:
        os.environ.pop("PROOFSIGNAL_CORE_CMD", None)
        os.environ["PROOFSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "empty-cache")
        self.addCleanup(lambda: os.environ.pop("PROOFSIGNAL_RUNTIME_CACHE_DIR", None))
        create_main_skill_coverage_workspace(self.project)
        before = (self.project / ".proofsignal" / "use-cases" / "profile-view-unauth.yaml").read_text(encoding="utf-8")

        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--json"])

        assert code == 2, err
        payload = json.loads(out)
        assert payload["status"] == "blocked"
        assert payload["managedRuntimeReadiness"]["blockers"][0]["repairable"] is False
        after = (self.project / ".proofsignal" / "use-cases" / "profile-view-unauth.yaml").read_text(encoding="utf-8")
        assert after == before

