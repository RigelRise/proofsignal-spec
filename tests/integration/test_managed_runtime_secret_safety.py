from __future__ import annotations

import json

from helpers import CliTestCase
from proofsignal_spec.runtime.distribution import normalize_platform
from tests.fixtures.managed_runtime import build_managed_runtime_distribution, serve_fake_entitlement_backend


class ManagedRuntimeSecretSafetyTests(CliTestCase):
    def test_init_output_and_project_state_do_not_contain_email_token_receipt_or_signed_url(self) -> None:
        import os

        os.environ.pop("PROOFSIGNAL_CORE_CMD", None)
        os.environ["PROOFSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "user-cache")
        os.environ["PROOFSIGNAL_EMAIL_UNLOCK_TOKEN"] = "ps_valid"
        os.environ["PROOFSIGNAL_EMAIL"] = "person@example.com"
        os.environ["PROOFSIGNAL_CORE_VERSION"] = "0.5.1"
        self.addCleanup(lambda: os.environ.pop("PROOFSIGNAL_RUNTIME_CACHE_DIR", None))
        self.addCleanup(lambda: os.environ.pop("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN", None))
        self.addCleanup(lambda: os.environ.pop("PROOFSIGNAL_EMAIL", None))
        self.addCleanup(lambda: os.environ.pop("PROOFSIGNAL_API_BASE_URL", None))
        self.addCleanup(lambda: os.environ.pop("PROOFSIGNAL_CORE_VERSION", None))
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=normalize_platform() or "darwin-arm64")
        with serve_fake_entitlement_backend(distribution) as (api_base_url, _state):
            os.environ["PROOFSIGNAL_API_BASE_URL"] = api_base_url
            code, out, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])

        assert code == 0, err
        workspace_text = "\n".join(path.read_text(encoding="utf-8") for path in (self.project / ".proofsignal").rglob("*") if path.is_file())
        payload = json.loads(out)
        text = json.dumps(payload) + workspace_text
        assert "person@example.com" not in text
        assert "ps_valid" not in text
        assert "signed-receipt" not in text
        assert "downloadUrl" not in text

