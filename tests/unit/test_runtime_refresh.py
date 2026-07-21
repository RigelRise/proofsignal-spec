from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import json

from verifysignal_spec.runtime.entitlement import (
    ensure_entitlement,
    load_refresh_credential,
    refresh_credential_path,
    refresh_pending_key_path,
    resolve_entitlement_config,
    save_receipt,
    save_refresh_credential,
)
from verifysignal_spec.runtime.models import RuntimeEntitlementReceipt
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


def _iso(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _place_receipt(status: str, expires_at: str) -> None:
    save_receipt(
        RuntimeEntitlementReceipt.from_dict(
            {
                "receiptId": "rcpt_old",
                "status": status,
                "expiresAt": expires_at,
                "issuer": "https://verifysignal.io",
                "keyId": "ps-entitlement-2026-06",
                "scopes": ["runtime.download", "runtime.local-use"],
                "usePolicy": {
                    "policyId": "public-free",
                    "policyVersion": 1,
                    "validationMode": "happy-path-only",
                    "maxUseCases": 1,
                },
            }
        )
    )


def _paths(state) -> list[str]:
    return [request["path"] for request in state.requests]


def test_exchange_bootstraps_and_stores_refresh_credential_0600(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    with serve_fake_entitlement_backend() as (api_base_url, _state):
        status = ensure_entitlement(
            config=resolve_entitlement_config(api_base_url=api_base_url),
            token="email-token-secret-123",
        )
    assert status.status == "valid"
    assert load_refresh_credential() == "vs_refresh_credential_fixture_0000000000"
    assert (refresh_credential_path().stat().st_mode & 0o777) == 0o600


def test_silent_refresh_renews_expired_receipt_without_email(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    _place_receipt("valid", "2000-01-01T00:00:00Z")
    save_refresh_credential("vs_refresh")

    with serve_fake_entitlement_backend() as (api_base_url, state):
        status = ensure_entitlement(config=resolve_entitlement_config(api_base_url=api_base_url))

    assert status.status == "valid"
    assert state.refresh_count == 1
    assert "/entitlements/refresh" in _paths(state)
    # The whole point: no email re-unlock.
    assert "/entitlements/exchange" not in _paths(state)


def test_proactive_refresh_when_near_expiry(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    _place_receipt("valid", _iso(datetime.now(UTC) + timedelta(hours=6)))
    save_refresh_credential("vs_refresh")

    with serve_fake_entitlement_backend() as (api_base_url, state):
        status = ensure_entitlement(config=resolve_entitlement_config(api_base_url=api_base_url))

    assert status.status == "valid"
    assert state.refresh_count == 1


def test_no_refresh_when_receipt_comfortably_valid(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    _place_receipt("valid", "2099-01-01T00:00:00Z")
    save_refresh_credential("vs_refresh")

    with serve_fake_entitlement_backend() as (api_base_url, state):
        status = ensure_entitlement(config=resolve_entitlement_config(api_base_url=api_base_url))

    assert status.status == "valid"
    # A comfortably valid receipt must not phone home on every run.
    assert state.refresh_count == 0


def test_expired_offline_shows_honest_reconnect_message(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    _place_receipt("valid", "2000-01-01T00:00:00Z")
    save_refresh_credential("vs_refresh")

    # Dead port → the refresh transport fails (api.unavailable), simulating offline.
    status = ensure_entitlement(config=resolve_entitlement_config(api_base_url="http://127.0.0.1:1/api"))

    assert status.status == "expired"
    assert "reconnect" in (status.message or "").lower()
    # The credential is a transient failure, NOT a rejection — it must be kept for the next attempt.
    assert refresh_credential_path().exists()


def test_refresh_sends_persistent_idempotency_key_and_clears_on_success(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    _place_receipt("valid", "2000-01-01T00:00:00Z")
    save_refresh_credential("vs_refresh")

    # Attempt 1: offline (dead port) → transient failure → the pending key survives for the retry.
    ensure_entitlement(config=resolve_entitlement_config(api_base_url="http://127.0.0.1:1/api"))
    assert refresh_pending_key_path().exists()
    pending = json.loads(refresh_pending_key_path().read_text(encoding="utf-8"))["idempotencyKey"]

    # Attempt 2 (retry): the SAME key is sent, so the backend can replay instead of double-minting;
    # success clears the pending key.
    with serve_fake_entitlement_backend() as (api_base_url, state):
        status = ensure_entitlement(config=resolve_entitlement_config(api_base_url=api_base_url))
    refresh_payloads = [r["payload"] for r in state.requests if r.get("path") == "/entitlements/refresh"]

    assert status.status == "valid"
    assert refresh_payloads and refresh_payloads[0]["idempotencyKey"] == pending
    assert not refresh_pending_key_path().exists()


def test_dead_credential_is_discarded(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    monkeypatch.delenv("VERIFYSIGNAL_EMAIL_UNLOCK_TOKEN", raising=False)
    _place_receipt("valid", "2000-01-01T00:00:00Z")
    save_refresh_credential("vs_refresh_revoked")

    with serve_fake_entitlement_backend() as (api_base_url, _state):
        ensure_entitlement(config=resolve_entitlement_config(api_base_url=api_base_url))

    # A rejected credential is dead: discard it so we fall back to the email path, not retry forever.
    assert not refresh_credential_path().exists()
