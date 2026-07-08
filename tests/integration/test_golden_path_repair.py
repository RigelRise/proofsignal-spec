from __future__ import annotations

import json
import os

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_productization import PUBLIC_ALIAS, create_golden_path_workspace


class GoldenPathRepairIntegrationTests(CliTestCase):
    def test_repairable_first_run_failure_emits_auto_repair_feedback(self) -> None:
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "aborted-activity-wait"
        create_golden_path_workspace(self.project)
        self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")

        code, out, err = self.cli(["repair", PUBLIC_ALIAS, "--project", str(self.project), "--from-report", str(report), "--json"])

        self.assertEqual(code, 0, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "applied")
        self.assertEqual(repair["recommendations"][0]["autonomy"], "auto-applied")
        self.assertEqual(repair["repairFeedback"][0]["autonomy"], "auto-applied")
        self.assertEqual(repair["stageCards"][0]["statusMarker"], "[REPAIR]")
