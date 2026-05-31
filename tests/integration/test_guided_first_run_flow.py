from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_onboarding import PUBLIC_ALIAS, create_onboarding_repository
from proofsignal_spec.workspace.repository import load_document


class GuidedFirstRunFlowIntegrationTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        create_onboarding_repository(self.project)

    def test_accept_persists_guided_state_with_stage_cards(self) -> None:
        code, out, err = self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        state = load_document(self.project / ".proofsignal/workflows/golden-path-state.yaml", default={})

        self.assertEqual(state["schemaVersion"], "proofsignal-spec-guided-first-run/v1")
        self.assertEqual(state["selectedCandidate"], PUBLIC_ALIAS)
        self.assertEqual(state["stage"], "accepted")
        self.assertEqual(state["resumeCommand"], data["resumeCommand"])
        self.assertTrue(state["stageCards"])

    def test_skip_preserves_normal_manual_use_case_selection(self) -> None:
        code, out, err = self.cli(["workflow", "skip-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["stage"], "skipped")

        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])
        self.assertEqual(code, 0, err)
        recommendation = json.loads(out)
        self.assertEqual(recommendation["status"], "ready")

    def test_run_updates_guided_state_to_direct_pass(self) -> None:
        self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])
        import os

        old_mode = os.environ.get("FAKE_PROOFSIGNAL_MODE")
        os.environ["FAKE_PROOFSIGNAL_MODE"] = "full-coverage"
        try:
            code, out, err = self.cli(["run", PUBLIC_ALIAS, "--project", str(self.project), "--profile", "normal", "--json"])
        finally:
            if old_mode is None:
                os.environ.pop("FAKE_PROOFSIGNAL_MODE", None)
            else:
                os.environ["FAKE_PROOFSIGNAL_MODE"] = old_mode

        self.assertEqual(code, 0, err)
        state = load_document(self.project / ".proofsignal/workflows/golden-path-state.yaml", default={})
        self.assertIn(state["stage"], {"passed", "repaired-passed"})
        self.assertTrue(state["strictPass"])
        self.assertIn("stageCards", state)
