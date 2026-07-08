from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_productization import PUBLIC_ALIAS, create_golden_path_workspace


class GoldenPathWorkspaceStateContractTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        create_golden_path_workspace(self.project)
        self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])
        unrelated = self.project / ".verifysignal/use-cases/manual.yaml"
        unrelated.write_text('{"alias":"manual","title":"Manual","description":"Preserve me"}\n', encoding="utf-8")

    def test_inspect_workspace_state_json_contract(self) -> None:
        code, out, err = self.cli(["workflow", "inspect-golden-path-state", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        payload = json.loads(out)
        self.assertEqual(payload["schemaVersion"], "verifysignal-spec-golden-path-workspace-state/v1")
        self.assertEqual(payload["status"], "ready")
        self.assertEqual(payload["firstRunStatus"], "not-started")
        self.assertEqual(payload["firstRunState"]["schemaVersion"], "verifysignal-spec-guided-first-run/v1")
        self.assertEqual(payload["firstRunState"]["stage"], "accepted")
        self.assertIn("resumeCommand", payload["firstRunState"])
        self.assertTrue(any("golden-path-state" in path for path in payload["ownedArtifacts"]))
        self.assertTrue(any("manual.yaml" in path for path in payload["preservedArtifacts"]))
        self.assertTrue(payload["resetPreview"])
        self.assertIn("nextAction", payload)

    def test_reset_preview_is_read_only_and_confirm_preserves_unrelated_artifacts(self) -> None:
        state_path = self.project / ".verifysignal/workflows/golden-path-state.yaml"
        unrelated = self.project / ".verifysignal/use-cases/manual.yaml"

        preview_code, preview_out, preview_err = self.cli(["workflow", "reset-golden-path-state", "--project", str(self.project), "--preview", "--json"])
        self.assertEqual(preview_code, 0, preview_err)
        self.assertTrue(state_path.exists())
        self.assertTrue(unrelated.exists())
        self.assertEqual(json.loads(preview_out)["status"], "ready")

        confirm_code, confirm_out, confirm_err = self.cli(["workflow", "reset-golden-path-state", "--project", str(self.project), "--confirm", "--json"])
        self.assertEqual(confirm_code, 0, confirm_err)
        self.assertFalse(state_path.exists())
        self.assertTrue(unrelated.exists())
        self.assertEqual(json.loads(confirm_out)["status"], "reset")
