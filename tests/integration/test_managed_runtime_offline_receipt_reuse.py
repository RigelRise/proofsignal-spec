from __future__ import annotations

import json

from helpers import CliTestCase
from verifysignal_spec.runtime.distribution import normalize_platform
from tests.fixtures.managed_runtime import build_managed_runtime_distribution, serve_fake_entitlement_backend


class ManagedRuntimeOfflineReceiptReuseTests(CliTestCase):
    def test_check_reuses_cached_runtime_and_receipt_without_backend_or_token(self) -> None:
        self.patch_env("VERIFYSIGNAL_CORE_CMD", None)
        self.patch_env("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(self.project / "user-cache"))
        self.patch_env("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", "vs_valid")
        self.patch_env("VERIFYSIGNAL_CORE_VERSION", "0.5.1")
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=platform)
        with serve_fake_entitlement_backend(distribution) as (api_base_url, _state):
            self.patch_env("VERIFYSIGNAL_API_BASE_URL", api_base_url)
            first_code, _first_out, first_err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
        assert first_code == 0, first_err

        self.patch_env("VERIFYSIGNAL_API_BASE_URL", None)
        self.patch_env("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        code, out, err = self.cli(["check", "--project", str(self.project), "--json"])
        payload = json.loads(out)

        assert code == 0, err
        assert payload["managedRuntimeReadiness"]["source"] == "managed-cache"
        assert payload["managedRuntimeReadiness"]["entitlement"]["status"] == "valid"

    def patch_env(self, key: str, value: str | None) -> None:
        import os

        old = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
        self.addCleanup(lambda: os.environ.pop(key, None) if old is None else os.environ.__setitem__(key, old))

