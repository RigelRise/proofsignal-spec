from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_onboarding import (
    BRANCH_ALIAS,
    PUBLIC_ALIAS,
    create_onboarding_repository,
)


class FirstRunSuitabilityIntegrationTests(CliTestCase):
    def test_recommend_first_run_lists_branch_relevant_candidates_separately(self) -> None:
        create_onboarding_repository(self.project)

        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["recommendedCandidate"]["alias"], PUBLIC_ALIAS)
        self.assertEqual([item["candidateAlias"] for item in data["branchRelevantCandidates"]], [BRANCH_ALIAS])
        self.assertIn("first", data["recommendationText"].lower())
        self.assertIn("other", data["acceptancePrompt"].lower())
