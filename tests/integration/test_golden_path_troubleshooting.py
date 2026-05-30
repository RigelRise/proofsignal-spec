from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_productization import create_golden_path_workspace


class GoldenPathTroubleshootingIntegrationTests(CliTestCase):
    def test_missing_target_recommendation_returns_blocker_stage_card(self) -> None:
        create_golden_path_workspace(self.project, target="")

        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 2, err)
        payload = json.loads(out)
        self.assertEqual(payload["status"], "blocked")
        self.assertEqual(payload["targetStatus"], "missing")
        self.assertEqual(payload["stageCards"][0]["statusMarker"], "[BLOCKED]")
        self.assertIn("clarify", payload["nextAction"])

    def test_unreachable_target_recommendation_returns_recovery_action(self) -> None:
        create_golden_path_workspace(self.project, include_unreachable_target=True)

        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 2, err)
        payload = json.loads(out)
        self.assertEqual(payload["targetStatus"], "unreachable")
        self.assertIn("target", payload["stageCards"][0]["summary"].lower())
