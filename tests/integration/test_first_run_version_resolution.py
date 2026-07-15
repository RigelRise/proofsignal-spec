from __future__ import annotations

import json
import os

from helpers import CliTestCase
from tests.fixtures.managed_runtime import build_managed_runtime_distribution, serve_fake_entitlement_backend
from verifysignal_spec.runtime.distribution import normalize_platform

# RATCHET (the real first-run path must be walkable).
#
# The managed download is exact-match on coreVersion, and the ONLY writer of the persisted version
# (`save_core_configuration(version=compatibility.verifysignalVersion)`) reads it off an already-
# installed Core. So on a fresh machine the version could only come from a binary the download exists
# to fetch: a closed loop, dead-ending at `distribution.version-unspecified` whose three suggested
# recoveries each require already having what they are trying to obtain.
#
# It survived a green suite because EVERY managed-runtime test sets `VERIFYSIGNAL_CORE_VERSION` in
# setUp — so no test had ever walked the path a real first-time user walks. That is the gap this
# closes: these tests deliberately unset every override.


class FirstRunVersionResolutionTests(CliTestCase):
    def setUp(self) -> None:
        super().setUp()
        os.environ.pop("VERIFYSIGNAL_CORE_CMD", None)
        # Deliberately NO VERIFYSIGNAL_CORE_VERSION: that pin is what every other managed-runtime
        # test sets, and setting it here would re-hide the bug.
        os.environ.pop("VERIFYSIGNAL_CORE_VERSION", None)
        os.environ.pop("VERIFYSIGNAL_RUNTIME_MANIFEST_PATH", None)
        os.environ.pop("VERIFYSIGNAL_RUNTIME_MANIFEST_JSON", None)
        os.environ["VERIFYSIGNAL_RUNTIME_CACHE_DIR"] = str(self.project / "user-cache")
        os.environ["VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN"] = "vs_valid"

    def tearDown(self) -> None:
        for key in [
            "VERIFYSIGNAL_RUNTIME_CACHE_DIR",
            "VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN",
            "VERIFYSIGNAL_API_BASE_URL",
            "VERIFYSIGNAL_CORE_VERSION",
        ]:
            os.environ.pop(key, None)
        super().tearDown()

    def test_a_fresh_machine_with_no_pin_reaches_a_ready_runtime(self) -> None:
        # The documented onboarding command, on a machine that has nothing: no env pin, no workspace
        # version, no cache, no --core-cmd, no local Core. This is THE first-run path.
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=platform)
        with serve_fake_entitlement_backend(distribution) as (api_base_url, _state):
            os.environ["VERIFYSIGNAL_API_BASE_URL"] = api_base_url
            code, out, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])

        assert code == 0, err
        payload = json.loads(out)
        assert payload["runtime"]["status"] == "ready", payload["runtime"].get("blockers")
        assert payload["runtime"]["source"] == "managed-download"

    def test_an_explicit_pin_still_wins_over_the_resolved_latest(self) -> None:
        # Scope guard: resolving a version must not override a version the user chose. An operator
        # pinning an older Core for reproducibility must keep getting that Core.
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(
            self.project / "distribution", platform=platform, core_version="0.5.1"
        )
        with serve_fake_entitlement_backend(distribution) as (api_base_url, state):
            os.environ["VERIFYSIGNAL_API_BASE_URL"] = api_base_url
            os.environ["VERIFYSIGNAL_CORE_VERSION"] = "0.5.1"
            code, out, err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])
            latest_calls = [request for request in state.requests if "/runtimes/latest" in str(request.get("path", ""))]

        assert code == 0, err
        # With a pin present the client must not even ask — asking would be a needless round trip and
        # would risk the answer quietly winning.
        assert latest_calls == []

    def test_it_blocks_rather_than_guessing_when_the_backend_cannot_answer(self) -> None:
        # Fail closed. Blocking was always the CORRECT behaviour when no version can be resolved —
        # guessing yields opaque 404s from the exact-match download API. The bug was that blocking was
        # the ONLY outcome; it must remain the outcome when the backend genuinely has no release.
        platform = normalize_platform() or "darwin-arm64"
        distribution = build_managed_runtime_distribution(self.project / "distribution", platform=platform)
        with serve_fake_entitlement_backend(distribution) as (api_base_url, state):
            state.latest_status = "unavailable"
            os.environ["VERIFYSIGNAL_API_BASE_URL"] = api_base_url
            code, out, _err = self.cli(["init", str(self.project), "--integration", "codex", "--json"])

        payload = json.loads(out)
        assert payload["runtime"]["status"] != "ready"
        assert payload["runtime"]["blockers"], "blocking without a blocker leaves the user no next step"
