from __future__ import annotations

from pathlib import Path

from verifysignal_spec.runtime.distribution import RuntimeDistributionClient, load_verification_keys
from verifysignal_spec.runtime.entitlement import EntitlementClient, resolve_entitlement_config
from verifysignal_spec.runtime.models import REQUIRED_RUNTIME_BLOCKER_CODES
from tests.fixtures.managed_runtime import (
    build_managed_runtime_distribution,
    serve_fake_entitlement_backend,
)


def test_backend_token_delivery_and_exchange_contract_public_free_policy(monkeypatch, tmp_path: Path) -> None:
    with serve_fake_entitlement_backend() as (api_base_url, state):
        config = resolve_entitlement_config(api_base_url=api_base_url)
        client = EntitlementClient(config)

        delivery = client.request_email_token("person@example.com", integration="codex")
        exchange = client.exchange_token("vs_valid")

    assert delivery.blocker is None
    assert delivery.data["schema"] == "verifysignal.entitlement-token-delivery/v1"
    assert delivery.data["tokenPolicy"] == {
        "policyId": "public-free",
        "policyVersion": 1,
        "validationMode": "happy-path-only",
        "maxUseCases": 1,
        "maxExchanges": 1,
        "maxExchangesPerHour": 1,
        "defaultTokenTtlDays": 30,
        "defaultReceiptTtlDays": 7,
        "refresh": "request_new_token",
    }
    assert exchange.blocker is None
    assert exchange.receipt is not None
    assert exchange.receipt.receiptId.startswith("rcpt_")
    assert exchange.receipt.issuer == "https://verifysignal.io"
    assert exchange.receipt.usePolicy["policyId"] == "public-free"
    assert exchange.receipt.tokenPolicy["maxExchanges"] == 1
    assert exchange.receipt.receiptPayload is not None
    assert exchange.receipt.receiptPayload.startswith('{"schema":"verifysignal.entitlement-receipt/v1"')
    assert state.requests[0]["path"] == "/entitlements/request-token"
    assert state.requests[1]["path"] == "/entitlements/exchange"


def test_backend_exchange_failure_codes_are_stable(monkeypatch) -> None:
    with serve_fake_entitlement_backend() as (api_base_url, _state):
        client = EntitlementClient(resolve_entitlement_config(api_base_url=api_base_url))

        invalid = client.exchange_token("vs_invalid")
        expired = client.exchange_token("vs_expired")
        limited = client.exchange_token("vs_exchange_limit")
        throttled = client.exchange_token("vs_exchange_throttled")

    assert invalid.blocker and invalid.blocker.code == "entitlement.invalid-token"
    assert expired.blocker and expired.blocker.code == "entitlement.expired-token"
    assert limited.blocker and limited.blocker.code == "entitlement.exchange-limit"
    assert throttled.blocker and throttled.blocker.code == "entitlement.exchange-throttled"
    assert {"entitlement.exchange-limit", "entitlement.exchange-throttled"}.issubset(REQUIRED_RUNTIME_BLOCKER_CODES)


def test_runtime_download_authorization_contract_and_api_unavailable_mapping(tmp_path: Path) -> None:
    distribution = build_managed_runtime_distribution(tmp_path / "distribution", platform="darwin-arm64")
    with serve_fake_entitlement_backend(distribution) as (api_base_url, state):
        config = resolve_entitlement_config(api_base_url=api_base_url)
        entitlement = EntitlementClient(config).exchange_token("vs_valid").receipt
        assert entitlement is not None
        client = RuntimeDistributionClient(config)

        grant = client.authorize_runtime_download("0.5.1", "darwin-arm64", entitlement)
        state.download_status = "unavailable"
        unavailable = client.authorize_runtime_download("0.5.1", "darwin-arm64", entitlement)

    assert grant.blocker is None
    assert grant.data["schema"] == "verifysignal.runtime-download/v1"
    assert grant.data["package"]["sha256"] == distribution["sha256"]
    assert "downloadUrl" in grant.data["package"]
    assert unavailable.blocker and unavailable.blocker.code == "distribution.unavailable"


def test_public_verification_keys_are_fetched_and_cached(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    with serve_fake_entitlement_backend() as (api_base_url, _state):
        config = resolve_entitlement_config(api_base_url=api_base_url)
        client = RuntimeDistributionClient(config)
        keys = client.fetch_verification_keys(issuer="https://verifysignal.io")

    assert keys.blocker is None
    assert keys.data["schema"] == "verifysignal.entitlement-keys/v1"
    cached = load_verification_keys()
    assert cached is not None
    assert cached["sourceApiBaseUrl"] == api_base_url
    assert cached["issuer"] == "https://verifysignal.io"
    assert cached["retrievedAt"]
    assert cached["keys"][0]["keyId"] == "ps-entitlement-2026-06"
    assert cached["keys"][0]["publicKeyPem"].startswith("-----BEGIN PUBLIC KEY-----")


def test_malformed_public_verification_keys_map_to_trust_blocker(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("VERIFYSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    with serve_fake_entitlement_backend() as (api_base_url, state):
        state.keys_status = "malformed"
        client = RuntimeDistributionClient(resolve_entitlement_config(api_base_url=api_base_url))
        keys = client.fetch_verification_keys()

    assert keys.blocker is not None
    assert keys.blocker.code == "entitlement.keys-incompatible"
    assert load_verification_keys() is None
