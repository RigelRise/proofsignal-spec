from __future__ import annotations

import unittest

from helpers import SRC  # noqa: F401
from proofsignal_spec.workspace.validation import looks_secret, validate_no_secret_values


class SecretRedactionTests(unittest.TestCase):
    def test_secret_policy_detects_sensitive_fields_and_allows_dummy_values(self) -> None:
        self.assertTrue(looks_secret("abc123", "apiKey"))
        self.assertFalse(looks_secret("dummy", "password"))

    def test_nested_secret_detection(self) -> None:
        findings = validate_no_secret_values({"parameters": {"clientSecret": "real-secret-value"}})
        self.assertTrue(findings)
