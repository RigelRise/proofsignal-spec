from __future__ import annotations

import json

from helpers import CliTestCase


class GoldenPathOnboardingPrepareIntegrationTests(CliTestCase):
    def test_clean_repository_specify_check_reports_safe_auto_prepare(self) -> None:
        code, out, err = self.cli(["workflow", "check", "specify", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["recommendedAction"], "auto-prepare-understanding")
        self.assertEqual(data["onboardingPreparation"]["status"], "auto-preparable")
        self.assertEqual(data["onboardingPreparation"]["approvalReason"], "")
        self.assertIn("workflow check specify", data["resumeCommand"])

    def test_sensitive_boundary_blocker_shape_is_available_for_agents(self) -> None:
        code, out, err = self.cli(["workflow", "check", "specify", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        preparation = data["onboardingPreparation"]
        self.assertIn("approvalRequired", preparation)
        self.assertIn("approvalReason", preparation)
        self.assertIn("resumeCommand", preparation)
        self.assertIn("stageCards", data)
