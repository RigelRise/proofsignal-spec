from __future__ import annotations

from pathlib import Path

from proofsignal_spec.runtime.entitlement import exchange_email_token, load_receipt, receipt_status, resolve_entitlement_config, save_receipt
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


def test_email_token_exchange_stores_receipt_without_raw_token(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    token = "email-token-secret-123"

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        receipt = exchange_email_token(token, config=resolve_entitlement_config(api_base_url=api_base_url))
    save_receipt(receipt)
    loaded = load_receipt()

    assert loaded is not None
    assert loaded.receiptId.startswith("rcpt_")
    assert loaded.status == "valid"
    assert token not in (tmp_path / "cache" / "entitlement" / "receipt.json").read_text(encoding="utf-8")


def test_receipt_status_blocks_expired_and_revoked() -> None:
    assert receipt_status({"status": "valid", "expiresAt": "2099-01-01T00:00:00Z"}).status == "valid"
    assert receipt_status({"status": "valid", "expiresAt": "2000-01-01T00:00:00Z"}).status == "expired"
    assert receipt_status({"status": "revoked", "expiresAt": "2099-01-01T00:00:00Z"}).status == "revoked"
