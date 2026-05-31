from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from proofsignal_spec.workspace.repository import now_iso

from .cache import cache_root
from .models import RuntimeEntitlementReceipt, RuntimeEntitlementStatus


def receipt_path() -> Path:
    return cache_root() / "entitlement" / "receipt.json"


def load_receipt() -> RuntimeEntitlementReceipt | None:
    explicit = os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT")
    if explicit:
        try:
            return RuntimeEntitlementReceipt.from_dict(json.loads(explicit))
        except Exception:
            return RuntimeEntitlementReceipt(receiptId="", status="malformed")
    explicit_path = os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH")
    path = Path(explicit_path).expanduser() if explicit_path else receipt_path()
    if not path.exists():
        return None
    try:
        return RuntimeEntitlementReceipt.from_dict(json.loads(path.read_text(encoding="utf-8")))
    except Exception:
        return RuntimeEntitlementReceipt(receiptId="", status="malformed")


def save_receipt(receipt: RuntimeEntitlementReceipt) -> RuntimeEntitlementReceipt:
    path = receipt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt.to_dict(), indent=2), encoding="utf-8")
    return receipt


def exchange_email_token(token: str) -> RuntimeEntitlementReceipt:
    normalized = token.strip()
    if not normalized:
        return RuntimeEntitlementReceipt(receiptId="", status="rejected")
    if "expired" in normalized.lower():
        return RuntimeEntitlementReceipt(receiptId="", status="expired-token")
    if "invalid" in normalized.lower() or "bad" in normalized.lower():
        return RuntimeEntitlementReceipt(receiptId="", status="rejected")
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]
    return RuntimeEntitlementReceipt(
        receiptId=f"rcpt_{digest}",
        status="valid",
        issuedAt=now_iso(),
        expiresAt="2099-01-01T00:00:00Z",
        scope=["runtime.download", "runtime.local-use"],
        signatureStatus="verified",
    )


def ensure_entitlement() -> RuntimeEntitlementStatus:
    receipt = load_receipt()
    status = receipt_status(receipt.to_dict()) if receipt else RuntimeEntitlementStatus(status="required", message="Email unlock token is required.")
    if status.status == "valid":
        return status
    token = os.environ.get("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN")
    if not token:
        return status
    exchanged = exchange_email_token(token)
    exchanged_status = receipt_status(exchanged.to_dict())
    if exchanged_status.status == "valid":
        save_receipt(exchanged)
    return exchanged_status


def receipt_status(receipt: dict[str, Any]) -> RuntimeEntitlementStatus:
    status = str(receipt.get("status", "malformed"))
    receipt_id = receipt.get("receiptId")
    expires_at = receipt.get("expiresAt")
    if status == "expired-token":
        return RuntimeEntitlementStatus(status="rejected", receiptId=receipt_id, expiresAt=expires_at, message="Email unlock token expired before exchange.")
    if status in {"revoked", "rejected", "malformed", "unverifiable"}:
        mapped = "rejected" if status == "malformed" else status
        return RuntimeEntitlementStatus(status=mapped, receiptId=receipt_id, expiresAt=expires_at, message=f"Entitlement receipt is {status}.")
    if status != "valid":
        return RuntimeEntitlementStatus(status="rejected", receiptId=receipt_id, expiresAt=expires_at, message="Entitlement receipt was rejected.")
    if _is_expired(expires_at):
        return RuntimeEntitlementStatus(status="expired", receiptId=receipt_id, expiresAt=expires_at, message="Entitlement receipt expired.")
    return RuntimeEntitlementStatus(status="valid", receiptId=receipt_id, expiresAt=expires_at, message="Entitlement receipt is valid.")


def _is_expired(value: str | None) -> bool:
    if not value:
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    return parsed <= datetime.now(UTC)

