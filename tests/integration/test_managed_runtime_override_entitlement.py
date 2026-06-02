from __future__ import annotations

from helpers import FAKE_CORE
from proofsignal_spec.runtime.resolver import ensure_core_runtime


def test_override_core_is_ready_but_not_managed_entitlement_success(tmp_path) -> None:
    result = ensure_core_runtime(tmp_path, explicit_core_cmd=str(FAKE_CORE))
    payload = result.to_dict()

    assert payload["status"] == "ready"
    assert payload["source"] == "explicit"
    assert payload["entitlement"]["status"] == "not-required"
    assert payload["source"] != "managed-download"

