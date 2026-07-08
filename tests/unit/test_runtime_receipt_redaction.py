from __future__ import annotations

import json

from verifysignal_spec.runtime.models import RuntimeEntitlementReceipt, redact_runtime_payload


def test_receipt_payload_is_not_serialized_in_public_summary() -> None:
    receipt = RuntimeEntitlementReceipt(
        receiptId="rcpt_public_id",
        status="valid",
        issuer="https://verifysignal.io",
        expiresAt="2099-01-01T00:00:00Z",
        receiptPayload="signed-receipt::secret",
    )

    text = json.dumps(receipt.to_dict())

    assert "rcpt_public_id" in text
    assert "signed-receipt::secret" not in text


def test_redaction_removes_backend_error_body_and_signed_urls() -> None:
    payload = redact_runtime_payload({"backendErrorBody": {"message": "token ps_secret"}, "url": "https://example.invalid/file?signature=abc"})

    text = json.dumps(payload)
    assert "vs_secret" not in text
    assert "signature=abc" not in text
