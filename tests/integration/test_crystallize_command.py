from __future__ import annotations

import os
from pathlib import Path

from helpers import CliTestCase

from verifysignal_spec.commands import crystallize as crystallize_command


class CrystallizeCommandTests(CliTestCase):
    def _run_dir(self) -> Path:
        run_dir = self.project / ".verifysignal" / "runs" / "login" / "fake-run-1"
        run_dir.mkdir(parents=True, exist_ok=True)
        return run_dir

    def test_crystallize_routes_through_resolver_and_returns_core_fixture(self) -> None:
        result = crystallize_command.run(self.project, self._run_dir())

        self.assertEqual(result["operation"], "crystallize")
        self.assertEqual(result["status"], "passed")
        self.assertTrue(result["data"]["fixture"]["manifestPath"])

    def test_crystallize_blocks_when_core_does_not_advertise_the_capability(self) -> None:
        # `crystallize` is optional, so a compatible Core may simply not implement it. Without the
        # capability gate the resolver returns `ready` and Core dies on an unknown subcommand; the
        # caller deserves a capability blocker instead.
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "omits-crystallize"
        try:
            result = crystallize_command.run(self.project, self._run_dir())
        finally:
            os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)

        self.assertEqual(result["status"], "blocked")
        self.assertTrue(
            any(blocker.get("code") == "core.crystallize-unsupported" for blocker in result["blockers"]),
            result["blockers"],
        )

    def test_crystallize_blocks_via_resolver_when_core_incompatible(self) -> None:
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "incompatible"
        try:
            result = crystallize_command.run(self.project, self._run_dir())
        finally:
            os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)

        self.assertEqual(result["status"], "blocked")
        self.assertIn("managedRuntimeReadiness", result)

    def test_crystallize_surfaces_core_entitlement_rejection_rather_than_bypassing_it(self) -> None:
        # Crystallize reads PRIVATE run evidence, so it is entitlement-protected. With no valid
        # receipt cached, Core's own rejection must reach the caller — Spec must not pretend the
        # operation is free the way `discover` is.
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "requires-entitlement"
        try:
            result = crystallize_command.run(self.project, self._run_dir())
        finally:
            os.environ.pop("FAKE_VERIFYSIGNAL_MODE", None)

        self.assertEqual(result["status"], "blocked")

    def test_crystallize_cli_threads_out_and_uses_resolved_runtime_command(self) -> None:
        # Prove --out and --api-base-url are threaded through (not accept-and-ignore) and that the
        # adapter is built from the resolver's runtimeCommand rather than a bare PATH lookup.
        run_dir = self._run_dir()
        fake_core = os.environ["VERIFYSIGNAL_CORE_CMD"]
        captured: dict = {}

        class _ReadyRuntime:
            status = "ready"
            runtimeCommand = fake_core

        def _spy(project, *, explicit_core_cmd=None, api_base_url=None, context=None):
            captured.update(api_base_url=api_base_url, context=context)
            return _ReadyRuntime()

        original = crystallize_command.ensure_core_runtime
        crystallize_command.ensure_core_runtime = _spy  # type: ignore[assignment]
        try:
            code, out, err = self.cli(
                [
                    "crystallize",
                    str(run_dir),
                    "--out",
                    str(self.project / "fixtures" / "login"),
                    "--project",
                    str(self.project),
                    "--api-base-url",
                    "https://staging.example.test",
                    "--json",
                ]
            )
        finally:
            crystallize_command.ensure_core_runtime = original  # type: ignore[assignment]

        self.assertEqual(code, 0, err)
        self.assertEqual(captured["api_base_url"], "https://staging.example.test")
        # Protected context: crystallize must NOT ride the entitlement-free discover path.
        self.assertEqual(captured["context"], "crystallize")
        self.assertIn('"operation": "crystallize"', out)
        self.assertIn(str(self.project / "fixtures" / "login"), out)
