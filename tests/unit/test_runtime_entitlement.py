from __future__ import annotations

from pathlib import Path

from proofsignal_spec.runtime.entitlement import exchange_email_token, load_receipt, receipt_status, save_receipt


def test_email_token_exchange_stores_receipt_without_raw_token(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    token = "email-token-secret-123"

    receipt = exchange_email_token(token)
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

