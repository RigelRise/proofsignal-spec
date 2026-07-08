from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_onboarding import PUBLIC_ALIAS, create_onboarding_repository


class GuidedFirstRunFlowContractTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        create_onboarding_repository(self.project)

    def test_accept_records_guided_state_and_resume_semantics(self) -> None:
        code, out, err = self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["schemaVersion"], "verifysignal-spec-guided-first-run/v1")
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["stage"], "accepted")
        self.assertEqual(data["selectedCandidate"], PUBLIC_ALIAS)
        self.assertEqual(data["firstRunStatus"], "not-started")
        self.assertIn(PUBLIC_ALIAS, data["resumeCommand"])
        self.assertEqual(data["nextAction"], data["resumeCommand"])
        self.assertEqual(data["stageCards"][0]["statusMarker"], "[ACCEPTED]")

    def test_skip_records_guided_state_but_keeps_manual_selection_available(self) -> None:
        code, out, err = self.cli(["workflow", "skip-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["schemaVersion"], "verifysignal-spec-guided-first-run/v1")
        self.assertEqual(data["status"], "skipped")
        self.assertEqual(data["stage"], "skipped")
        self.assertEqual(data["firstRunStatus"], "skipped")
        self.assertIn("manual", data["nextAction"].lower())
        self.assertEqual(data["stageCards"][0]["statusMarker"], "[SKIPPED]")
