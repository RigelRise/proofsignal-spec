from __future__ import annotations

import json

from proofsignal_spec.runtime.consent import metadata_summary, resolve_metadata_consent
from proofsignal_spec.runtime.entitlement import exchange_email_token, resolve_entitlement_config, save_receipt
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


def test_email_token_exchange_persists_receipt_not_raw_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    token = "email-token-secret-contract"

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        receipt = exchange_email_token(token, config=resolve_entitlement_config(api_base_url=api_base_url))
    save_receipt(receipt)

    persisted = (tmp_path / "cache" / "entitlement" / "receipt.json").read_text(encoding="utf-8")
    assert token not in persisted
    persisted_data = json.loads(persisted)
    receipt_id = (
        persisted_data.get("receiptId")
        or persisted_data.get("receiptSummary", {}).get("receiptId")
        or persisted_data.get("claims", {}).get("receiptId")
    )
    assert receipt_id.startswith("rcpt_")


def test_metadata_consent_is_independent_from_entitlement(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_METADATA_CONSENT", "declined")

    decision = resolve_metadata_consent(tmp_path)
    summary = metadata_summary(tmp_path)

    assert decision.status == "declined"
    assert decision.blocksRuntimeUnlock is False
    assert summary["forbiddenCategoriesExcluded"] is True
