from __future__ import annotations

import json

from helpers import CliTestCase
from verifysignal_spec.runtime.distribution import normalize_platform
from tests.fixtures.managed_runtime import build_managed_runtime_distribution, serve_fake_entitlement_backend


class ManagedRuntimeEntitlementFailureTests(CliTestCase):
    def test_invalid_token_blocks_before_runtime_download(self) -> None:
        self.patch_env("VERIFYSIGNAL_CORE_CMD", None)
        self.patch_env("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(self.project / "user-cache"))
        self.patch_env("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", "vs_invalid")
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=normalize_platform() or "darwin-arm64")
        with serve_fake_entitlement_backend(distribution) as (api_base_url, state):
            self.patch_env("VERIFYSIGNAL_API_BASE_URL", api_base_url)
            code, out, _err = self.cli(["check", "--project", str(self.project), "--json"])
        payload = json.loads(out)

        assert code == 2
        assert payload["managedRuntimeReadiness"]["blockers"][0]["code"] == "entitlement.invalid-token"
        assert not any(request["path"].startswith("/runtimes/") for request in state.requests)

    def test_unauthorized_runtime_download_is_distribution_blocker(self) -> None:
        self.patch_env("VERIFYSIGNAL_CORE_CMD", None)
        self.patch_env("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(self.project / "user-cache"))
        self.patch_env("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", "vs_valid")
        self.patch_env("VERIFYSIGNAL_CORE_VERSION", "0.5.1")
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=normalize_platform() or "darwin-arm64")
        with serve_fake_entitlement_backend(distribution) as (api_base_url, state):
            state.download_status = "unauthorized"
            self.patch_env("VERIFYSIGNAL_API_BASE_URL", api_base_url)
            code, out, _err = self.cli(["check", "--project", str(self.project), "--json"])
        payload = json.loads(out)

        assert code == 2
        assert payload["managedRuntimeReadiness"]["blockers"][0]["code"] == "distribution.unauthorized"
        assert payload["managedRuntimeReadiness"]["blockers"][0]["repairable"] is False

    def patch_env(self, key: str, value: str | None) -> None:
        import os

        old = os.environ.get(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
        self.addCleanup(lambda: os.environ.pop(key, None) if old is None else os.environ.__setitem__(key, old))

