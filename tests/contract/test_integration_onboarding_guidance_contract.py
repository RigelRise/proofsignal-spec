from __future__ import annotations

import json

from helpers import CliTestCase
from tests.fixtures.workflows.golden_path_onboarding import assert_guidance_shape


class IntegrationOnboardingGuidanceContractTests(CliTestCase):
    def test_integration_install_returns_onboarding_guide_contract(self) -> None:
        code, out, err = self.cli(["integration", "install", "codex", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        guide = data["onboardingGuide"]
        assert_guidance_shape(guide)
        self.assertEqual(guide["schemaVersion"], "proofsignal-spec-onboarding-guidance/v1")
        self.assertEqual(guide["integrationKey"], "codex")
        self.assertIn("/proofsignal-specify", guide["nextCommand"])
        self.assertIn("[RECOMMENDED]", guide["stageMarkers"])
        self.assertIn("repaired", " ".join(guide["successSemantics"]).lower())
        self.assertIn("sensitive", " ".join(guide["safetyBoundaries"]).lower())
