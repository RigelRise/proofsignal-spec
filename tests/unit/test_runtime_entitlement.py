from __future__ import annotations

from pathlib import Path

import json
import time

from proofsignal_spec.runtime.distribution import prepare_verification_keys, save_verification_keys
from proofsignal_spec.runtime.entitlement import exchange_email_token, load_receipt, receipt_status, resolve_entitlement_config, save_receipt
from proofsignal_spec.runtime.models import RuntimeEntitlementStatus
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


def test_manual_public_key_override_precedence_requires_matching_receipt_key(monkeypatch) -> None:
    config = resolve_entitlement_config(api_base_url="http://localhost:3000/api")
    entitlement = RuntimeEntitlementStatus(
        status="valid",
        receiptId="rcpt_test",
        issuer="https://proofsignal.io",
        keyId="ps-entitlement-2026-06",
    )
    monkeypatch.setenv(
        "PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON",
        json.dumps([{"keyId": "ps-entitlement-2026-06", "algorithm": "ed25519", "publicKeyPem": "public", "status": "active"}]),
    )

    ready, blocker = prepare_verification_keys(config, entitlement)

    assert blocker is None
    assert ready.status == "ready"
    assert ready.source == "manual-override"
    assert ready.matchedKeyId == "ps-entitlement-2026-06"

    monkeypatch.setenv(
        "PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON",
        json.dumps([{"keyId": "other-key", "algorithm": "ed25519", "publicKeyPem": "public", "status": "active"}]),
    )

    blocked, blocker = prepare_verification_keys(config, entitlement)

    assert blocker is not None
    assert blocker.code == "entitlement.key-unknown"
    assert blocked.status == "blocked"
    assert blocked.source == "manual-override"
    assert blocked.blockerCode == "entitlement.key-unknown"


def test_matching_cached_public_keys_resolve_without_network_under_50ms(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON", raising=False)
    config = resolve_entitlement_config(api_base_url="http://localhost:3000/api")
    entitlement = RuntimeEntitlementStatus(
        status="valid",
        receiptId="rcpt_test",
        issuer="https://proofsignal.io",
        keyId="ps-entitlement-2026-06",
    )
    save_verification_keys(
        {
            "schema": "proofsignal.entitlement-keys/v1",
            "schemaVersion": 1,
            "keys": [{"keyId": "ps-entitlement-2026-06", "algorithm": "ed25519", "publicKeyPem": "public", "status": "active"}],
        },
        source_api_base_url=config.apiBaseUrl,
        issuer=entitlement.issuer,
    )

    started = time.perf_counter()
    status, blocker = prepare_verification_keys(config, entitlement)
    elapsed = time.perf_counter() - started

    assert blocker is None
    assert status.status == "ready"
    assert status.source == "cache"
    assert elapsed < 0.05
