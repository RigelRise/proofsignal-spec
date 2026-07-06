from __future__ import annotations

import json
import os

from helpers import CliTestCase
from proofsignal_spec.runtime.distribution import normalize_platform
from tests.fixtures.managed_runtime import build_managed_runtime_distribution, serve_fake_entitlement_backend


class RuntimeCacheReuseTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ.pop("PROOFSIGNAL_CORE_CMD", None)
        os.environ["PROOFSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "user-cache")
        os.environ["PROOFSIGNAL_EMAIL_UNLOCK_TOKEN"] = "ps_valid"
        os.environ["PROOFSIGNAL_CORE_VERSION"] = "0.5.1"

    def tearDown(self) -> None:
        os.environ.pop("PROOFSIGNAL_RUNTIME_CACHE_DIR", None)
        os.environ.pop("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        os.environ.pop("PROOFSIGNAL_API_BASE_URL", None)
        os.environ.pop("PROOFSIGNAL_CORE_VERSION", None)
        super().tearDown()

    def test_second_init_reuses_verified_cache_without_manifest_or_token(self) -> None:
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=platform)
        with serve_fake_entitlement_backend(distribution) as (api_base_url, _state):
            os.environ["PROOFSIGNAL_API_BASE_URL"] = api_base_url
            first_code, first_out, first_err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        assert first_code == 0, first_err
        assert json.loads(first_out)["runtime"]["source"] == "managed-download"

        os.environ.pop("PROOFSIGNAL_API_BASE_URL", None)
        os.environ.pop("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        second_code, second_out, second_err = self.cli(["init", str(self.project), "--integration", "claude", "--json"])

        assert second_code == 0, second_err
        assert json.loads(second_out)["runtime"]["source"] == "managed-cache"
