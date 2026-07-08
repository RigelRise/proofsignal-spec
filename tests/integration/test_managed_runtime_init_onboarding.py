from __future__ import annotations

import json
import os
from pathlib import Path

from helpers import CliTestCase
from verifysignal_spec.runtime.distribution import normalize_platform
from tests.fixtures.managed_runtime import build_managed_runtime_distribution, serve_fake_entitlement_backend


class ManagedRuntimeInitOnboardingTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ.pop("VERIFYSIGNAL_CORE_CMD", None)
        os.environ["VERIFYSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "user-cache")
        os.environ["VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN"] = "vs_valid"
        os.environ["VERIFYSIGNAL_CORE_VERSION"] = "0.5.1"

    def tearDown(self) -> None:
        os.environ.pop("VERIFYSIGNAL_RUNTIME_CACHE_DIR", None)
        os.environ.pop("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", None)
        os.environ.pop("VERIFYSIGNAL_API_BASE_URL", None)
        os.environ.pop("VERIFYSIGNAL_CORE_VERSION", None)
        super().tearDown()

    def test_init_manages_runtime_without_manual_core_setup(self) -> None:
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=platform)
        with serve_fake_entitlement_backend(distribution) as (api_base_url, _state):
            os.environ["VERIFYSIGNAL_API_BASE_URL"] = api_base_url
            code, out, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])

        assert code == 0, err
        payload = json.loads(out)
        assert payload["runtime"]["status"] == "ready"
        assert payload["runtime"]["source"] == "managed-download"
        assert payload["core"]["compatible"] is True
        workspace_text = (self.project / ".verifysignal" / "workspace.yaml").read_text(encoding="utf-8")
        guide_text = (self.project / ".agents" / "VERIFYSIGNAL_ONBOARDING.md").read_text(encoding="utf-8")
        assert "vs_valid" not in workspace_text + guide_text + out
        assert "core setup" not in guide_text.lower()
