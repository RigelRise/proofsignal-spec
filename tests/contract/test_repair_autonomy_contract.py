from __future__ import annotations

import json
import os

from helpers import CliTestCase


class RepairAutonomyContractTests(CliTestCase):
    def test_wait_strategy_report_auto_applies_as_safe_mechanical_repair(self) -> None:
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "aborted-activity-wait"
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "home-page-unauth", "Validate home page.", "--project", str(self.project)])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")

        code, out, err = self.cli(["repair", "home-page-unauth", "--project", str(self.project), "--from-report", str(report), "--json"])

        self.assertEqual(code, 0, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "applied")
        self.assertEqual(repair["recommendations"][0]["autonomy"], "auto-applied")
        self.assertTrue(repair["recommendations"][0]["safeMechanical"])
        self.assertFalse(repair["recommendations"][0]["requiresUserDecision"])
        self.assertEqual(repair["applications"][0]["validationStatus"], "not-run")
        self.assertEqual(repair["stageCards"][0]["statusMarker"], "[REPAIR]")

    def test_gate_mapping_repair_still_requires_confirmation(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "home-page-unauth", "Validate home page.", "--project", str(self.project)])
        record_path = self.project / ".proofsignal/use-cases/home-page-unauth.yaml"
        data = json.loads(record_path.read_text(encoding="utf-8"))
        data["validation"] = {
            "findings": [
                {
                    "code": "missing-gateid",
                    "message": "assertion lacks gateId",
                    "artifact": ".proofsignal/skills/home-page-unauth.browser.md",
                    "path": "assertions[0]",
                }
            ]
        }
        record_path.write_text(json.dumps(data), encoding="utf-8")

        code, out, _err = self.cli(["repair", "home-page-unauth", "--project", str(self.project), "--json"])

        self.assertEqual(code, 4)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "pending")
        self.assertEqual(repair["recommendations"][0]["autonomy"], "confirmation-required")
        self.assertTrue(repair["recommendations"][0]["requiresUserDecision"])
