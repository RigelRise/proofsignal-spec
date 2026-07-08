from __future__ import annotations

import json

from verifysignal_spec.runtime.models import (
    REQUIRED_RUNTIME_BLOCKER_CODES,
    ManagedRuntimeReadinessResult,
    RuntimeApiStatus,
    RuntimeEntitlementStatus,
    RuntimeSetupBlocker,
)


def test_readiness_shape_includes_api_and_valid_receipt_summary_without_payload() -> None:
    result = ManagedRuntimeReadinessResult(
        status="ready",
        source="managed-cache",
        runtimeCommand="/cache/verifysignal-core",
        api=RuntimeApiStatus(baseUrl="https://verifysignal.io/api", source="default", status="reachable"),
        entitlement=RuntimeEntitlementStatus(
            status="valid",
            receiptId="rcpt_123",
            issuer="https://verifysignal.io",
            expiresAt="2099-01-01T00:00:00Z",
        ),
    )

    payload = result.to_dict()
    text = json.dumps(payload)

    assert payload["api"] == {"baseUrl": "https://verifysignal.io/api", "source": "default", "status": "reachable"}
    assert payload["entitlement"]["issuer"] == "https://verifysignal.io"
    assert "signed-receipt" not in text


def test_required_entitlement_distribution_blockers_are_public_and_not_repairable() -> None:
    expected = {
        "api.unavailable",
        "api.incompatible",
        "api.misconfigured",
        "network.missing",
        "platform.unsupported",
        "entitlement.unlock-required",
        "entitlement.delivery-unavailable",
        "entitlement.delivery-throttled",
        "entitlement.invalid-token",
        "entitlement.expired-token",
        "entitlement.exchange-limit",
        "entitlement.exchange-throttled",
        "entitlement.expired",
        "entitlement.revoked",
        "entitlement.malformed",
        "entitlement.unverifiable",
        "entitlement.rejected",
        "distribution.unauthorized",
        "distribution.unavailable",
        "distribution.url-expired",
        "manifest.invalid",
        "artifact.integrity-failed",
        "artifact.authenticity-failed",
        "cache.permission-denied",
        "core.incompatible",
    }

    assert expected.issubset(REQUIRED_RUNTIME_BLOCKER_CODES)
    blocker = RuntimeSetupBlocker(code="entitlement.exchange-limit", message="Exchange limit reached.")
    payload = blocker.to_dict()

    assert payload["category"] == "entitlement"
    assert payload["repairable"] is False

