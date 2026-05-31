from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_onboarding import (
    BRANCH_ALIAS,
    PUBLIC_ALIAS,
    create_onboarding_repository,
    no_ideal_inventory,
)


class FirstRunSuitabilityContractTests(CliTestCase):
    def test_recommendation_prefers_public_low_risk_candidate_over_branch_relevance(self) -> None:
        create_onboarding_repository(self.project)

        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["schemaVersion"], "proofsignal-spec-first-run-recommendation/v1")
        self.assertEqual(data["status"], "ready")
        self.assertEqual(data["recommendedCandidate"]["alias"], PUBLIC_ALIAS)
        self.assertFalse(data["explicitAcceptanceRequired"])
        self.assertEqual(data["recommendedCandidate"]["idealCriteriaMissing"], [])
        self.assertIn("highly recommended", data["acceptancePrompt"].lower())

        ranked = {item["candidateAlias"]: item for item in data["rankedCandidates"]}
        self.assertIn(PUBLIC_ALIAS, ranked)
        self.assertIn(BRANCH_ALIAS, ranked)
        self.assertLess(ranked[PUBLIC_ALIAS]["rank"], ranked[BRANCH_ALIAS]["rank"])
        self.assertFalse(ranked[PUBLIC_ALIAS]["branchRelevant"])
        self.assertTrue(ranked[BRANCH_ALIAS]["branchRelevant"])
        self.assertIn("readOnly", ranked[BRANCH_ALIAS]["idealCriteriaMissing"])
        self.assertEqual(ranked[PUBLIC_ALIAS]["sourceInventoryItems"], ["route-home"])

        branch_aliases = [item["candidateAlias"] for item in data["branchRelevantCandidates"]]
        self.assertEqual(branch_aliases, [BRANCH_ALIAS])

    def test_no_ideal_candidate_requires_explicit_acceptance_and_lists_gaps(self) -> None:
        create_onboarding_repository(self.project, inventory=no_ideal_inventory())

        code, out, err = self.cli(["workflow", "recommend-first-run", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertEqual(data["status"], "ready")
        self.assertTrue(data["explicitAcceptanceRequired"])
        self.assertTrue(data["recommendedCandidate"]["requiresExplicitAcceptance"])
        self.assertIn("idealCriteriaMissing", data["recommendedCandidate"])
        self.assertIn("explicit", data["acceptancePrompt"].lower())
