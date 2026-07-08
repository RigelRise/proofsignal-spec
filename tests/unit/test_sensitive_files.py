from __future__ import annotations

import unittest

from helpers import SRC  # noqa: F401
from verifysignal_spec.workspace.sensitive_files import filter_safe_paths, is_sensitive_path


class SensitiveFileTests(unittest.TestCase):
    def test_default_patterns_block_secret_files(self) -> None:
        self.assertTrue(is_sensitive_path(".env.local"))
        self.assertTrue(is_sensitive_path("config/client-secret.json"))
        self.assertFalse(is_sensitive_path("src/app.py"))

    def test_filter_splits_safe_and_blocked_paths(self) -> None:
        safe, blocked = filter_safe_paths(["README.md", ".env", "src/main.py"])
        self.assertEqual(safe, ["README.md", "src/main.py"])
        self.assertEqual(blocked, [".env"])
