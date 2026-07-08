from __future__ import annotations

from pathlib import Path

from verifysignal_spec.runtime.entitlement import load_receipt, receipt_path, receipt_status, resolve_entitlement_config, save_receipt
from verifysignal_spec.runtime.entitlement import EntitlementClient
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


def test_receipt_storage_uses_user_cache_permissions_and_summary(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    with serve_fake_entitlement_backend() as (api_base_url, _state):
        receipt = EntitlementClient(resolve_entitlement_config(api_base_url=api_base_url)).exchange_token("vs_valid").receipt
    assert receipt is not None

    saved = save_receipt(receipt)
    path = receipt_path()

    assert str(tmp_path / "cache") in str(path)
    assert str(path) == saved.path
    assert path.stat().st_mode & 0o077 == 0
    assert path.read_text(encoding="utf-8").startswith('{"schema":"verifysignal.entitlement-receipt/v1"')
    assert load_receipt() is not None
    assert receipt_status(saved).status == "valid"


def test_expired_receipt_requires_refresh_without_raw_token_persistence() -> None:
    status = receipt_status({"receiptSummary": {"receiptId": "rcpt_expired", "status": "valid", "expiresAt": "2000-01-01T00:00:00Z"}})

    assert status.status == "expired"
    assert status.blockerCode == "entitlement.expired"
