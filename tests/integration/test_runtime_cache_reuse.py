from __future__ import annotations

import json
import os

from helpers import CliTestCase
from proofsignal_spec.runtime.distribution import normalize_platform
from tests.fixtures.managed_runtime import build_managed_runtime_distribution


class RuntimeCacheReuseTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ.pop("PROOFSIGNAL_CORE_CMD", None)
        os.environ["PROOFSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "user-cache")
        os.environ["PROOFSIGNAL_EMAIL_UNLOCK_TOKEN"] = "email-token-cache-reuse"

    def tearDown(self) -> None:
        os.environ.pop("PROOFSIGNAL_RUNTIME_CACHE_DIR", None)
        os.environ.pop("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        os.environ.pop("PROOFSIGNAL_RUNTIME_MANIFEST_PATH", None)
        super().tearDown()

    def test_second_init_reuses_verified_cache_without_manifest_or_token(self) -> None:
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=platform)
        os.environ["PROOFSIGNAL_RUNTIME_MANIFEST_PATH"] = str(distribution["manifest"])

        first_code, first_out, first_err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        assert first_code == 0, first_err
        assert json.loads(first_out)["runtime"]["source"] == "managed-download"

        os.environ.pop("PROOFSIGNAL_RUNTIME_MANIFEST_PATH", None)
        os.environ.pop("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        second_code, second_out, second_err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])

        assert second_code == 0, second_err
        assert json.loads(second_out)["runtime"]["source"] == "managed-cache"

