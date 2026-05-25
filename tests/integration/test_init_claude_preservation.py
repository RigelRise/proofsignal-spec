from __future__ import annotations

from helpers import CliTestCase


class InitClaudePreservationTests(CliTestCase):
    def test_modified_claude_file_is_preserved_on_rerun(self) -> None:
        self.assertEqual(self.cli(["init", str(self.project), "--integration", "claude", "--json"])[0], 0)
        skill = self.project / ".claude" / "skills" / "proofsignal-spec-author" / "SKILL.md"
        skill.write_text("user modified\n", encoding="utf-8")
        self.assertEqual(self.cli(["init", str(self.project), "--integration", "claude", "--json"])[0], 0)
        self.assertEqual(skill.read_text(encoding="utf-8"), "user modified\n")
