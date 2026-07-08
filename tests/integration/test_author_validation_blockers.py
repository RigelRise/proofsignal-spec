from __future__ import annotations

import os

from helpers import CliTestCase


class AuthorValidationBlockerTests(CliTestCase):
    def test_validation_blocker_marks_use_case_blocked(self) -> None:
        self.cli(["init", str(self.project), "--integration", "codex"])
        self.cli(["author", "login", "Validate login.", "--project", str(self.project)])
        os.environ["FAKE_VERIFYSIGNAL_MODE"] = "blocked"
        code, _, _ = self.cli(["validate", "login", "--project", str(self.project)])
        self.assertEqual(code, 2)
