from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_productization import PUBLIC_ALIAS, create_golden_path_workspace


class GoldenPathFirstRunIntegrationTests(CliTestCase):
    def test_real_target_first_recommend_accept_and_skip_semantics(self) -> None:
        create_golden_path_workspace(self.project)

        recommend_code, recommend_out, recommend_err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])
        self.assertEqual(recommend_code, 0, recommend_err)
        recommendation = json.loads(recommend_out)
        self.assertEqual(recommendation["recommendedCandidate"]["alias"], PUBLIC_ALIAS)

        accept_code, accept_out, accept_err = self.cli(["workflow", "accept-first-run", PUBLIC_ALIAS, "--project", str(self.project), "--json"])
        self.assertEqual(accept_code, 0, accept_err)
        accepted = json.loads(accept_out)
        self.assertEqual(accepted["status"], "accepted")
        self.assertEqual(accepted["stageCards"][0]["statusMarker"], "[ACCEPTED]")

        skip_code, skip_out, skip_err = self.cli(["workflow", "skip-first-run", "--project", str(self.project), "--json"])
        self.assertEqual(skip_code, 0, skip_err)
        skipped = json.loads(skip_out)
        self.assertEqual(skipped["status"], "skipped")
        self.assertNotIn(skipped["status"], {"passed", "failed", "incomplete"})
