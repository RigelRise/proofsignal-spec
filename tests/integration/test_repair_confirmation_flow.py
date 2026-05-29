from __future__ import annotations

import json

from helpers import CliTestCase
from proofsignal_spec.workspace.repository import load_use_case, save_use_case
from tests.fixtures.workflows.main_skill_run_coverage import create_main_skill_coverage_workspace


class RepairConfirmationFlowTests(CliTestCase):
    def test_ambiguous_selector_feedback_requires_confirmation_before_change(self) -> None:
        create_main_skill_coverage_workspace(self.project)
        record = load_use_case(self.project, "profile-view-unauth")
        record.validation = {
            "findings": [
                {
                    "code": "strict-mode-violation",
                    "message": "Profile card locator resolved to multiple elements.",
                    "artifact": ".proofsignal/skills/profile.browser.md",
                    "path": "targets.profileCard",
                }
            ]
        }
        save_use_case(self.project, record)

        code, out, err = self.cli(["repair", "profile-view-unauth", "--project", str(self.project), "--approve", "--json"])

        self.assertEqual(code, 0, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "conflict")
        self.assertFalse(repair["readyForRun"])
        self.assertTrue(repair["recommendations"][0]["requiresUserDecision"])
        self.assertEqual(repair["recommendations"][0]["safeCategory"], "selector-ambiguity")

    def test_broad_confirmation_is_recorded_after_root_cause_and_scope(self) -> None:
        import os

        os.environ["FAKE_PROOFSIGNAL_MODE"] = "aborted-activity-wait"
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "home-page-unauth", "Validate home page.", "--project", str(self.project)])
        report = self.project / "report.json"
        report.write_text("{}", encoding="utf-8")

        code, out, err = self.cli(["repair", "home-page-unauth", "--project", str(self.project), "--from-report", str(report), "--approve", "--json"])

        self.assertEqual(code, 0, err)
        repair = json.loads(out)["repair"]
        self.assertEqual(repair["approvalStatus"], "approved")
        self.assertEqual(repair["repairConfirmations"][0]["category"], "wait-flow-issue")
        self.assertEqual(repair["repairConfirmations"][0]["confirmationSource"], "explicit-command")
        self.assertTrue(repair["repairConfirmations"][0]["revalidationRequired"])
        self.assertEqual(repair["revalidation"]["status"], "not-run")
