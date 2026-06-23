from __future__ import annotations

import unittest
from pathlib import Path

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import core_supports_discover
from proofsignal_spec.integrations.base import WORKFLOW_COMMANDS, render_workflow_skill_files
from proofsignal_spec.workflows.models import WORKFLOW_STAGES
from proofsignal_spec.workflows.stage_persistence import PERSISTABLE_STAGES


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


class CoreSupportsDiscoverTests(unittest.TestCase):
    def test_true_when_discover_advertised(self) -> None:
        response = _version_response(
            [
                {"name": "run", "schema": "proofsignal.run/v1"},
                {"name": "discover", "schema": "proofsignal.discover/v1", "status": "experimental"},
            ]
        )
        self.assertTrue(core_supports_discover(response))

    def test_false_when_absent(self) -> None:
        response = _version_response([{"name": "run", "schema": "proofsignal.run/v1"}])
        self.assertFalse(core_supports_discover(response))

    def test_false_on_wrong_schema(self) -> None:
        response = _version_response([{"name": "discover", "schema": "proofsignal.discover/v2"}])
        self.assertFalse(core_supports_discover(response))

    def test_false_on_malformed(self) -> None:
        self.assertFalse(core_supports_discover({}))
        self.assertFalse(core_supports_discover({"data": {"operations": "nope"}}))


class AutoCommandRegistrationTests(unittest.TestCase):
    def test_auto_installed_for_both_agents_as_bare_proofsignal(self) -> None:
        for agent, root in (("Claude", ".claude/skills"), ("Codex", ".agents/skills")):
            paths = [rendered.path for rendered in render_workflow_skill_files(root, agent)]
            self.assertIn(f"{root}/proofsignal/SKILL.md", paths)
            self.assertNotIn(f"{root}/proofsignal-auto/SKILL.md", paths)

    def test_auto_is_a_command_not_a_persistable_stage(self) -> None:
        command_stages = [spec.stage for spec in WORKFLOW_COMMANDS]
        self.assertIn("auto", command_stages)
        self.assertNotIn("auto", WORKFLOW_STAGES)
        self.assertNotIn("auto", PERSISTABLE_STAGES)


if __name__ == "__main__":
    unittest.main()
