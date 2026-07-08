from __future__ import annotations

import json
import os

from helpers import CliTestCase
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


class RuntimeDistributionFailureTests(CliTestCase):
    def tearDown(self) -> None:
        os.environ.pop("VERIFYSIGNAL_RUNTIME_CACHE_DIR", None)
        os.environ.pop("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        os.environ.pop("VERIFYSIGNAL_API_BASE_URL", None)
        os.environ.pop("VERIFYSIGNAL_RUNTIME_MANIFEST_JSON", None)
        super().tearDown()

    def test_invalid_manifest_blocks_without_invoking_runtime(self) -> None:
        os.environ.pop("VERIFYSIGNAL_CORE_CMD", None)
        os.environ["VERIFYSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "empty-cache")
        os.environ["VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN"] = "vs_valid"
        os.environ["VERIFYSIGNAL_RUNTIME_MANIFEST_JSON"] = '{"entries": []}'

        with serve_fake_entitlement_backend() as (api_base_url, _state):
            os.environ["VERIFYSIGNAL_API_BASE_URL"] = api_base_url
            code, out, _err = self.cli(["check", "--project", str(self.project), "--json"])

        assert code == 2
        payload = json.loads(out)
        blockers = payload["managedRuntimeReadiness"]["blockers"]
        assert blockers[0]["code"] == "manifest.invalid"
        assert blockers[0]["repairable"] is False
