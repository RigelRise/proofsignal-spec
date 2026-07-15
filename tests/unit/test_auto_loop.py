from __future__ import annotations

import unittest
from pathlib import Path

from verifysignal_spec.core.adapter import CoreAdapter
from verifysignal_spec.core.contracts import core_supports_crystallize, core_supports_discover
from verifysignal_spec.integrations.base import WORKFLOW_COMMANDS, render_workflow_skill_files
from verifysignal_spec.workflows.models import WORKFLOW_STAGES
from verifysignal_spec.workflows.stage_persistence import PERSISTABLE_STAGES


class _CapturingAdapter(CoreAdapter):
    """Capture the argv passed to Core without spawning a subprocess."""

    def __init__(self) -> None:
        super().__init__(executable="x")
        self.calls: list[tuple[list[str], dict | None]] = []

    def require_compatible(self):  # type: ignore[override]
        return None

    def _run(self, args, env=None):  # type: ignore[override]
        self.calls.append((args, env))
        return {"status": "passed", "data": {}}


def _version_response(operations: list[dict]) -> dict:
    return {"data": {"operations": operations}}


class AutoLoopAdapterTests(unittest.TestCase):
    def test_discover_builds_expected_argv(self) -> None:
        adapter = _CapturingAdapter()
        adapter.discover(url="http://127.0.0.1:3120", skill=Path("draft.browser.md"))
        args, _ = adapter.calls[-1]
        self.assertEqual(args, ["discover", "--url", "http://127.0.0.1:3120", "--skill", "draft.browser.md", "--json"])

    def test_discover_passes_headed_flag(self) -> None:
        adapter = _CapturingAdapter()
        adapter.discover(url="http://x", skill=Path("s.md"), headed=True)
        args, _ = adapter.calls[-1]
        self.assertIn("--headed", args)

    def test_crystallize_builds_expected_argv(self) -> None:
        adapter = _CapturingAdapter()
        adapter.crystallize(run_dir=Path(".verifysignal/runs/login/fake-run-1"))
        args, _ = adapter.calls[-1]
        self.assertEqual(args, ["crystallize", ".verifysignal/runs/login/fake-run-1", "--json"])

    def test_crystallize_passes_out_dir(self) -> None:
        adapter = _CapturingAdapter()
        adapter.crystallize(run_dir=Path("run"), out=Path("fixtures/out"))
        args, _ = adapter.calls[-1]
        self.assertEqual(args, ["crystallize", "run", "--out", "fixtures/out", "--json"])

    def test_run_passes_record_and_replay_flags(self) -> None:
        adapter = _CapturingAdapter()
        adapter.run(
            run_request=Path("req.yaml"),
            main_skill=Path("main.browser.md"),
            skills=[Path("main.browser.md")],
            record=True,
            replay=Path("fixtures/login"),
        )
        args, _ = adapter.calls[-1]
        self.assertIn("--record", args)
        self.assertEqual(args[args.index("--replay") + 1], "fixtures/login")
        # additive flags land before the trailing --json sentinel
        self.assertEqual(args[-1], "--json")
        self.assertLess(args.index("--record"), args.index("--json"))
        self.assertLess(args.index("--replay"), args.index("--json"))

    def test_run_omits_record_and_replay_by_default(self) -> None:
        adapter = _CapturingAdapter()
        adapter.run(
            run_request=Path("req.yaml"),
            main_skill=Path("main.browser.md"),
            skills=[Path("main.browser.md")],
        )
        args, _ = adapter.calls[-1]
        self.assertNotIn("--record", args)
        self.assertNotIn("--replay", args)


class CoreSupportsDiscoverTests(unittest.TestCase):
    def test_true_when_discover_advertised(self) -> None:
        response = _version_response(
            [
                {"name": "run", "schema": "verifysignal.run/v1"},
                {"name": "discover", "schema": "verifysignal.discover/v1", "status": "experimental"},
            ]
        )
        self.assertTrue(core_supports_discover(response))

    def test_false_when_absent(self) -> None:
        response = _version_response([{"name": "run", "schema": "verifysignal.run/v1"}])
        self.assertFalse(core_supports_discover(response))

    def test_false_on_wrong_schema(self) -> None:
        response = _version_response([{"name": "discover", "schema": "verifysignal.discover/v2"}])
        self.assertFalse(core_supports_discover(response))

    def test_false_on_malformed(self) -> None:
        self.assertFalse(core_supports_discover({}))
        self.assertFalse(core_supports_discover({"data": {"operations": "nope"}}))


class CoreSupportsCrystallizeTests(unittest.TestCase):
    def test_true_when_crystallize_advertised(self) -> None:
        response = _version_response(
            [
                {"name": "run", "schema": "verifysignal.run/v1"},
                {"name": "crystallize", "schema": "verifysignal.crystallize/v1", "status": "experimental"},
            ]
        )
        self.assertTrue(core_supports_crystallize(response))

    def test_false_when_absent(self) -> None:
        response = _version_response([{"name": "run", "schema": "verifysignal.run/v1"}])
        self.assertFalse(core_supports_crystallize(response))

    def test_false_on_wrong_schema(self) -> None:
        response = _version_response([{"name": "crystallize", "schema": "verifysignal.crystallize/v2"}])
        self.assertFalse(core_supports_crystallize(response))

    def test_false_on_malformed(self) -> None:
        self.assertFalse(core_supports_crystallize({}))
        self.assertFalse(core_supports_crystallize({"data": {"operations": "nope"}}))


class AutoCommandRegistrationTests(unittest.TestCase):
    def test_auto_installed_for_both_agents_as_bare_verifysignal(self) -> None:
        for agent, root in (("Claude", ".claude/skills"), ("Codex", ".agents/skills")):
            paths = [rendered.path for rendered in render_workflow_skill_files(root, agent)]
            self.assertIn(f"{root}/verifysignal/SKILL.md", paths)
            self.assertNotIn(f"{root}/verifysignal-auto/SKILL.md", paths)

    def test_auto_is_a_command_not_a_persistable_stage(self) -> None:
        command_stages = [spec.stage for spec in WORKFLOW_COMMANDS]
        self.assertIn("auto", command_stages)
        self.assertNotIn("auto", WORKFLOW_STAGES)
        self.assertNotIn("auto", PERSISTABLE_STAGES)


if __name__ == "__main__":
    unittest.main()
