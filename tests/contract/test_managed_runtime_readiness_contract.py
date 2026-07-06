from __future__ import annotations

import json

from proofsignal_spec.core.contracts import REQUIRED_OPERATION_METADATA
from proofsignal_spec.runtime.models import (
    MANAGED_RUNTIME_READINESS_SCHEMA,
    REQUIRED_RUNTIME_BLOCKER_CODES,
    ManagedRuntimeReadinessResult,
    RuntimeSetupBlocker,
    RuntimeSourceAttempt,
)


def test_managed_runtime_readiness_shape_and_operations() -> None:
    result = ManagedRuntimeReadinessResult(
        status="ready",
        source="managed-cache",
        runtimeCommand="/tmp/proofsignal-core",
        runtimeVersion="0.5.1",
        contractVersion="proofsignal-public-cli-json/v1",
        attempts=[
            RuntimeSourceAttempt(
                source="managed-cache",
                status="compatible",
                terminal=True,
                runtimeVersion="0.5.1",
                message="Verified cached runtime is compatible.",
            )
        ],
    )

    payload = result.to_dict()

    assert payload["schemaVersion"] == MANAGED_RUNTIME_READINESS_SCHEMA
    assert payload["status"] == "ready"
    assert payload["source"] == "managed-cache"
    assert payload["requiredOperations"] == REQUIRED_OPERATION_METADATA
    assert payload["requiredOperationsByName"]["report.inspect"]["schemaName"] == "proofsignal.report-inspection/v1"
    assert payload["attempts"][0]["source"] == "managed-cache"
    assert payload["blockers"] == []


def test_all_required_blocker_codes_are_structured_and_not_repairable() -> None:
    assert {
        "network.missing",
        "manifest.unavailable",
        "manifest.invalid",
        "platform.unsupported",
        "artifact.integrity-failed",
        "artifact.authenticity-failed",
        "cache.permission-denied",
        "credentials.unavailable",
        "entitlement.unlock-required",
        "entitlement.invalid-token",
        "entitlement.expired-token",
        "entitlement.expired",
        "entitlement.revoked",
        "entitlement.rejected",
        "core.incompatible",
        "distribution.unavailable",
    }.issubset(REQUIRED_RUNTIME_BLOCKER_CODES)
    blocker = RuntimeSetupBlocker(code="entitlement.unlock-required", message="Token required.")

    payload = blocker.to_dict()

    assert payload["severity"] == "blocker"
    assert payload["repairable"] is False
    assert payload["category"] == "entitlement"


def test_runtime_readiness_serialization_redacts_secret_values() -> None:
    result = ManagedRuntimeReadinessResult(
        status="blocked",
        blockers=[
            RuntimeSetupBlocker(
                code="manifest.unavailable",
                message="Could not fetch https://download.example/runtime?X-Amz-Signature=secret-signature",
            )
        ],
    )

    serialized = json.dumps(result.to_dict())

    assert "secret-signature" not in serialized
    assert "[redacted]" in serialized

