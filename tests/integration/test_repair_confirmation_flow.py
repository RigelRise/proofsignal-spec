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
