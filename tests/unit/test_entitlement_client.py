from __future__ import annotations

import json

from proofsignal_spec.runtime.entitlement import DEFAULT_API_BASE_URL, EntitlementClient, resolve_entitlement_config
from proofsignal_spec.runtime.models import redact_runtime_payload
from tests.fixtures.managed_runtime import serve_fake_entitlement_backend


def test_entitlement_config_defaults_to_production_and_reports_override_sources(monkeypatch) -> None:
    monkeypatch.delenv("PROOFSIGNAL_API_BASE_URL", raising=False)
    default = resolve_entitlement_config()
    flag = resolve_entitlement_config(api_base_url="http://localhost:3000/api")
    monkeypatch.setenv("PROOFSIGNAL_API_BASE_URL", "http://127.0.0.1:9999/api")
    env = resolve_entitlement_config()

    assert default.apiBaseUrl == DEFAULT_API_BASE_URL
    assert default.source == "default"
    assert flag.source == "flag"
    assert env.source == "environment"


def test_entitlement_client_validates_exchange_schema_and_public_free_policy() -> None:
    with serve_fake_entitlement_backend() as (api_base_url, _state):
        exchange = EntitlementClient(resolve_entitlement_config(api_base_url=api_base_url)).exchange_token("ps_valid")

    assert exchange.blocker is None
    assert exchange.receipt is not None
    assert exchange.receipt.issuer == "https://proofsignal.io"
    assert exchange.receipt.usePolicy["policyId"] == "public-free"
    assert exchange.receipt.tokenPolicy["maxExchanges"] == 1
    assert exchange.receipt.tokenPolicy["maxExchangesPerHour"] == 1
    assert exchange.receipt.receiptPayload
    assert exchange.receipt.receiptPayload.startswith('{"schema":"proofsignal.entitlement-receipt/v1"')


def test_entitlement_redaction_removes_email_token_receipt_and_backend_details() -> None:
    payload = redact_runtime_payload(
        {
            "email": "person@example.com",
            "token": "ps_secret_token",
            "tokenPolicy": {"maxExchanges": 3, "maxExchangesPerHour": 3, "ttlDays": 30},
            "receipt": "signed-receipt::secret",
            "backendErrorBody": {"signedUrl": "https://example.invalid/runtime?signature=abc"},
            "safe": "api unavailable",
        }
    )

    text = json.dumps(payload)
    assert "person@example.com" not in text
    assert "ps_secret_token" not in text
    assert "signed-receipt::secret" not in text
    assert "signature=abc" not in text
    assert payload["tokenPolicy"]["maxExchanges"] == 3
    assert payload["safe"] == "api unavailable"
