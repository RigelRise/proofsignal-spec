from __future__ import annotations

import json

from proofsignal_spec.runtime.consent import metadata_summary, resolve_metadata_consent
from proofsignal_spec.runtime.entitlement import exchange_email_token, save_receipt


def test_email_token_exchange_persists_receipt_not_raw_token(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    token = "email-token-secret-contract"

    receipt = exchange_email_token(token)
    save_receipt(receipt)

    persisted = (tmp_path / "cache" / "entitlement" / "receipt.json").read_text(encoding="utf-8")
    assert token not in persisted
    assert json.loads(persisted)["receiptId"].startswith("rcpt_")


def test_metadata_consent_is_independent_from_entitlement(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_METADATA_CONSENT", "declined")

    decision = resolve_metadata_consent(tmp_path)
    summary = metadata_summary(tmp_path)

    assert decision.status == "declined"
    assert decision.blocksRuntimeUnlock is False
    assert summary["forbiddenCategoriesExcluded"] is True

