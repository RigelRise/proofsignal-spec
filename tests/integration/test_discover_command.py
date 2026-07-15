from __future__ import annotations

import os
from pathlib import Path

from helpers import CliTestCase

from verifysignal_spec.commands import discover as discover_command


class DiscoverCommandTests(CliTestCase):
    def _skill(self) -> Path:
        skill_dir = self.project / ".verifysignal" / "skills"
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill = skill_dir / "draft.browser.md"
        skill.write_text("# draft\n", encoding="utf-8")
        return skill

    def test_discover_routes_through_resolver_and_returns_core_grounding(self) -> None:
        # The Core must ADVERTISE verifysignal.discover/v1 for the resolver to route discover to it
        # (the real Core does — see its operation contract). The fake's default "ok" mode models an
        # older Core that implements discover without advertising it, which the resolver now refuses
        # rather than invoking and crashing on an unknown subcommand.
        skill = self._skill()
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "advertises-discover"
        try:
            result = discover_command.run(self.project, "https://app.example.test/en", skill)
        finally:
            os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)
        self.assertEqual(result["operation"], "discover")
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["data"]["url"], "https://app.example.test/en")
        self.assertTrue(result["data"]["groundedTargets"])

    def test_discover_blocks_via_resolver_when_core_incompatible(self) -> None:
        # The old handler called CoreAdapter.discover directly, whose require_compatible()
        # RAISES on an incompatible core. Routing through ensure_core_runtime yields a
        # structured blocked payload instead, proving discover now uses the managed resolver.
        skill = self._skill()
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "incompatible"
        try:
            result = discover_command.run(self.project, "https://app.example.test/en", skill)
        finally:
            os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)
        self.assertEqual(result["status"], "blocked")
        self.assertIn("managedRuntimeReadiness", result)

    def test_discover_cli_threads_api_base_url_and_uses_resolved_runtime_command(self) -> None:
        # Stronger than "argparse accepts the flag": prove --api-base-url is threaded to the
        # managed resolver (not accept-and-ignore) AND that the Core adapter is built from the
        # resolver's runtimeCommand (not a bare `verifysignal` on PATH). A spy on the resolver
        # captures both. If discover reverted to a direct CoreAdapter, the spy would never run —
        # `captured` stays empty and the api_base_url assertion raises KeyError.
        skill = self._skill()
        fake_core = os.environ["VERIFYSIGNAL_CORE_CMD"]
        captured: dict = {}

        class _ReadyRuntime:
            status = "ready"
            runtimeCommand = fake_core

        def _spy(project, *, explicit_core_cmd=None, api_base_url=None, context=None):
            captured.update(api_base_url=api_base_url, context=context)
            return _ReadyRuntime()

        original = discover_command.ensure_core_runtime
        discover_command.ensure_core_runtime = _spy  # type: ignore[assignment]
        try:
            code, out, err = self.cli(
                [
                    "discover",
                    "--url",
                    "https://app.example.test/en",
                    "--skill",
                    str(skill),
                    "--project",
                    str(self.project),
                    "--api-base-url",
                    "https://staging.example.test",
                    "--json",
                ]
            )
        finally:
            discover_command.ensure_core_runtime = original  # type: ignore[assignment]

        self.assertEqual(code, 0, err)
        # --api-base-url reached the resolver under the discover context (fails on accept-and-ignore).
        self.assertEqual(captured["api_base_url"], "https://staging.example.test")
        self.assertEqual(captured["context"], "discover")
        # The adapter was built from the resolver's runtimeCommand -> real grounding output.
        self.assertIn('"operation": "discover"', out)
        self.assertIn('"status": "passed"', out)
