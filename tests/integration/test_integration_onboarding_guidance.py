from __future__ import annotations

import json

from helpers import CliTestCase


class IntegrationOnboardingGuidanceIntegrationTests(CliTestCase):
    def test_codex_install_prints_guidance_and_writes_local_guide(self) -> None:
        code, out, err = self.cli(["integration", "install", "codex", "--project", str(self.project)])

        self.assertEqual(code, 0, err)
        self.assertIn("ProofSignal Golden Path", out)
        self.assertIn("[RECOMMENDED]", out)
        self.assertIn("/proofsignal-specify", out)

        guide_path = self.project / ".agents" / "PROOFSIGNAL_ONBOARDING.md"
        self.assertTrue(guide_path.exists())
        content = guide_path.read_text(encoding="utf-8")
        self.assertIn("Safety Boundaries", content)
        self.assertIn("Repaired strict pass", content)

    def test_claude_install_prints_guidance_and_writes_local_guide(self) -> None:
        code, out, err = self.cli(["integration", "install", "claude", "--project", str(self.project)])

        self.assertEqual(code, 0, err)
        self.assertIn("ProofSignal Golden Path", out)
        self.assertIn("[PASS]", out)

        guide_path = self.project / ".claude" / "PROOFSIGNAL_ONBOARDING.md"
        self.assertTrue(guide_path.exists())
        self.assertIn("/proofsignal-specify", guide_path.read_text(encoding="utf-8"))

    def test_upgrade_includes_guidance_for_each_result(self) -> None:
        code, out, err = self.cli(["integration", "upgrade", "--project", str(self.project), "--json"])

        self.assertEqual(code, 0, err)
        data = json.loads(out)
        self.assertTrue(data["upgraded"])
        self.assertTrue(all("onboardingGuide" in item for item in data["upgraded"]))
