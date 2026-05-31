from __future__ import annotations

import json
import os

from helpers import CliTestCase


class RuntimeDistributionFailureTests(CliTestCase):
    def tearDown(self) -> None:
        os.environ.pop("PROOFSIGNAL_RUNTIME_CACHE_DIR", None)
        os.environ.pop("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        os.environ.pop("PROOFSIGNAL_RUNTIME_MANIFEST_JSON", None)
        super().tearDown()

    def test_invalid_manifest_blocks_without_invoking_runtime(self) -> None:
        os.environ.pop("PROOFSIGNAL_CORE_CMD", None)
        os.environ["PROOFSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "empty-cache")
        os.environ["PROOFSIGNAL_EMAIL_UNLOCK_TOKEN"] = "email-token-for-manifest-shape"
        os.environ["PROOFSIGNAL_RUNTIME_MANIFEST_JSON"] = '{"entries": []}'

        code, out, _err = self.cli(["check", "--project", str(self.project), "--json"])

        assert code == 2
        payload = json.loads(out)
        blockers = payload["managedRuntimeReadiness"]["blockers"]
        assert blockers[0]["code"] == "manifest.invalid"
        assert blockers[0]["repairable"] is False
