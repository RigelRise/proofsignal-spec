from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_productization import PUBLIC_ALIAS, create_golden_path_workspace


class GoldenPathWorkspaceStateIntegrationTests(CliTestCase):
    def test_inspect_empty_resume_and_reset_flow(self) -> None:
        create_golden_path_workspace(self.project)

        empty_code, empty_out, empty_err = self.cli(["workflow", "inspect-golden-path-state", "--project", str(self.project), "--json"])
        self.assertEqual(empty_code, 0, empty_err)
        self.assertEqual(json.loads(empty_out)["status"], "empty")

        self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])
        inspect_code, inspect_out, inspect_err = self.cli(["workflow", "inspect-golden-path-state", "--project", str(self.project), "--json"])
        self.assertEqual(inspect_code, 0, inspect_err)
        payload = json.loads(inspect_out)
        self.assertEqual(payload["status"], "ready")
        self.assertIn(PUBLIC_ALIAS, payload["resumeHint"])
        self.assertEqual(payload["firstRunState"]["selectedCandidate"], PUBLIC_ALIAS)
        self.assertEqual(payload["firstRunState"]["stage"], "accepted")

        reset_code, reset_out, reset_err = self.cli(["workflow", "reset-golden-path-state", "--project", str(self.project), "--confirm", "--json"])
        self.assertEqual(reset_code, 0, reset_err)
        self.assertEqual(json.loads(reset_out)["status"], "reset")
