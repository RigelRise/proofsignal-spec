from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_productization import PUBLIC_ALIAS, create_golden_path_workspace


class FirstRunRecommendationContractTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        create_golden_path_workspace(self.project)

    def test_recommend_first_run_json_contract(self) -> None:
        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["schemaVersion"], "proofsignal-spec-first-run-recommendation/v1")
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["targetStatus"], "resolved")
        self.assertEqual(data["recommendedCandidate"]["alias"], PUBLIC_ALIAS)
        self.assertIn("strongly recommend", data["recommendationText"].lower())
        self.assertIn("highly recommended", data["acceptancePrompt"].lower())
        self.assertIn("not a pass", data["skipMeaning"])
        self.assertEqual(data["stageCards"][0]["statusMarker"], "[RECOMMENDED]")
        self.assertIn("accept-first-run", data["nextAction"])

    def test_accept_first_run_json_contract(self) -> None:
        code, out, err = self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["schemaVersion"], "proofsignal-spec-guided-first-run/v1")
        self.assertEqual(data["status"], "accepted")
        self.assertEqual(data["stage"], "accepted")
        self.assertEqual(data["selectedCandidate"], PUBLIC_ALIAS)
        self.assertEqual(data["selectedCandidateDetails"]["alias"], PUBLIC_ALIAS)
        self.assertEqual(data["stageCards"][0]["statusMarker"], "[ACCEPTED]")
        self.assertIn(PUBLIC_ALIAS, data["resumeCommand"])

    def test_skip_first_run_json_contract(self) -> None:
        code, out, err = self.cli(["workflow", "skip-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["schemaVersion"], "proofsignal-spec-guided-first-run/v1")
        self.assertEqual(data["status"], "skipped")
        self.assertEqual(data["stage"], "skipped")
        self.assertIn("not success", data["skipMeaning"])
        self.assertEqual(data["stageCards"][0]["statusMarker"], "[SKIPPED]")
        self.assertIn("nextAction", data)
