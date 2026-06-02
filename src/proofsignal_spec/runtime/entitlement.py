from __future__ import annotations

import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from proofsignal_spec import __version__

from .cache import cache_root
from .distribution import normalize_platform
from .models import (
    EntitlementClientConfig,
    RuntimeEntitlementReceipt,
    RuntimeEntitlementStatus,
    RuntimeSetupBlocker,
)

DEFAULT_API_BASE_URL = "https://proofsignal.io/api"
PRODUCTION_RECEIPT_ISSUER = "https://proofsignal.io"
DEFAULT_HTTP_TIMEOUT_SECONDS = 30
MIN_HTTP_TIMEOUT_SECONDS = 1
MAX_HTTP_TIMEOUT_SECONDS = 120


@dataclass(slots=True)
class EntitlementResponse:
    data: dict[str, Any]
    blocker: RuntimeSetupBlocker | None = None


@dataclass(slots=True)
class TokenExchangeResponse:
    receipt: RuntimeEntitlementReceipt | None = None
    data: dict[str, Any] | None = None
    blocker: RuntimeSetupBlocker | None = None


def resolve_entitlement_config(
    *,
    api_base_url: str | None = None,
    workspace_api_base_url: str | None = None,
    source: str | None = None,
    timeout_seconds: int | None = None,
) -> EntitlementClientConfig:
    env_url = os.environ.get("PROOFSIGNAL_API_BASE_URL")
    env_timeout = os.environ.get("PROOFSIGNAL_API_TIMEOUT_SECONDS")
    if api_base_url:
        resolved = api_base_url
        resolved_source = source or "flag"
    elif env_url:
        resolved = env_url
        resolved_source = source or "environment"
    elif workspace_api_base_url:
        resolved = workspace_api_base_url
        resolved_source = source or "workspace"
    else:
        resolved = DEFAULT_API_BASE_URL
        resolved_source = source or "default"
    timeout = timeout_seconds
    if timeout is None and env_timeout:
        try:
            timeout = int(env_timeout)
        except ValueError:
            timeout = DEFAULT_HTTP_TIMEOUT_SECONDS
    timeout = max(MIN_HTTP_TIMEOUT_SECONDS, min(MAX_HTTP_TIMEOUT_SECONDS, int(timeout or DEFAULT_HTTP_TIMEOUT_SECONDS)))
    _validate_api_base_url(resolved)
    return EntitlementClientConfig(
        apiBaseUrl=resolved.rstrip("/"),
        source=resolved_source,  # type: ignore[arg-type]
        timeoutSeconds=timeout,
        cliVersion=__version__,
        platform=normalize_platform(),
    )


def receipt_path() -> Path:
    explicit = os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return cache_root() / "entitlement" / "receipt.json"


def load_receipt() -> RuntimeEntitlementReceipt | None:
    explicit = os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT") or os.environ.get("PROOFSIGNAL_ENTITLEMENT_RECEIPT_PATH")
    path = Path(explicit).expanduser() if explicit else receipt_path()
    if not path.exists():
        return None
    try:
        text = path.read_text(encoding="utf-8").strip()
        data = json.loads(text)
        if isinstance(data, dict) and data.get("schema") == "proofsignal.entitlement-receipt/v1":
            receipt = RuntimeEntitlementReceipt.from_raw_receipt_payload(text)
        else:
            receipt = RuntimeEntitlementReceipt.from_dict(data)
        receipt.path = str(path)
        return receipt
    except Exception:
        return RuntimeEntitlementReceipt(receiptId="", status="malformed", path=str(path))


def save_receipt(receipt: RuntimeEntitlementReceipt) -> RuntimeEntitlementReceipt:
    path = receipt_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    if receipt.receiptPayload:
        path.write_text(receipt.receiptPayload, encoding="utf-8")
    else:
        path.write_text(json.dumps(receipt.to_file_dict(), indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    receipt.path = str(path)
    return receipt


def receipt_status(receipt: dict[str, Any] | RuntimeEntitlementReceipt) -> RuntimeEntitlementStatus:
    parsed = receipt if isinstance(receipt, RuntimeEntitlementReceipt) else RuntimeEntitlementReceipt.from_dict(receipt)
    status = parsed.status
    if status == "expired-token":
        return RuntimeEntitlementStatus(
            status="rejected",
            receiptId=parsed.receiptId,
            expiresAt=parsed.expiresAt,
            message="Email unlock token expired before exchange.",
            blockerCode="entitlement.expired-token",
        )
    if status in {"revoked", "rejected", "malformed", "unverifiable"}:
        return RuntimeEntitlementStatus(
            status=status,  # type: ignore[arg-type]
            receiptId=parsed.receiptId,
            issuer=parsed.issuer,
            expiresAt=parsed.expiresAt,
            scopes=list(parsed.scopes),
            keyId=parsed.keyId,
            usePolicy=dict(parsed.usePolicy),
            tokenPolicy=dict(parsed.tokenPolicy),
            message=f"Entitlement receipt is {status}.",
            blockerCode=f"entitlement.{status}",
            receiptPath=parsed.path,
        )
    if status != "valid":
        return RuntimeEntitlementStatus(
            status="rejected",
            receiptId=parsed.receiptId,
            expiresAt=parsed.expiresAt,
            message="Entitlement receipt was rejected.",
            blockerCode="entitlement.rejected",
            receiptPath=parsed.path,
        )
    if _is_expired(parsed.expiresAt):
        return RuntimeEntitlementStatus(
            status="expired",
            receiptId=parsed.receiptId,
            issuer=parsed.issuer,
            expiresAt=parsed.expiresAt,
            scopes=list(parsed.scopes),
            keyId=parsed.keyId,
            usePolicy=dict(parsed.usePolicy),
            tokenPolicy=dict(parsed.tokenPolicy),
            message="Entitlement receipt expired.",
            blockerCode="entitlement.expired",
            receiptPath=parsed.path,
        )
    status_result = parsed.to_status()
    status_result.message = "Entitlement receipt is valid."
    return status_result


def ensure_entitlement(
    *,
    config: EntitlementClientConfig | None = None,
    email: str | None = None,
    token: str | None = None,
    request_delivery: bool = False,
    integration: str | None = None,
) -> RuntimeEntitlementStatus:
    receipt = load_receipt()
    status = receipt_status(receipt) if receipt else RuntimeEntitlementStatus(status="required", message="Email unlock token is required.", blockerCode="entitlement.unlock-required")
    if status.status == "valid":
        return status
    config = config or resolve_entitlement_config()
    client = EntitlementClient(config)
    raw_token = token or os.environ.get("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN")
    if raw_token:
        exchanged = client.exchange_token(raw_token)
        if exchanged.blocker:
            return RuntimeEntitlementStatus(status="rejected", message=exchanged.blocker.message, blockerCode=exchanged.blocker.code)
        if exchanged.receipt:
            saved = save_receipt(exchanged.receipt)
            return receipt_status(saved)
    delivery_email = email or os.environ.get("PROOFSIGNAL_EMAIL")
    if request_delivery and delivery_email:
        delivery = client.request_email_token(delivery_email, integration=integration)
        if delivery.blocker:
            return RuntimeEntitlementStatus(status="required", message=delivery.blocker.message, blockerCode=delivery.blocker.code)
        return RuntimeEntitlementStatus(status="token-delivery-pending", message="Email unlock token delivery was requested.", blockerCode="entitlement.unlock-required")
    return status


def exchange_email_token(token: str, *, config: EntitlementClientConfig | None = None) -> RuntimeEntitlementReceipt:
    """Compatibility wrapper for tests and older callers.

    Production code should use EntitlementClient.exchange_token() so backend
    failure blockers are preserved. This wrapper still returns a receipt object.
    """
    result = EntitlementClient(config or resolve_entitlement_config()).exchange_token(token)
    if result.receipt:
        return result.receipt
    blocker = result.blocker
    status = "expired-token" if blocker and blocker.code == "entitlement.expired-token" else "rejected"
    return RuntimeEntitlementReceipt(receiptId="", status=status)


class EntitlementClient:
    def __init__(self, config: EntitlementClientConfig | None = None) -> None:
        self.config = config or resolve_entitlement_config()

    def request_email_token(self, email: str, *, integration: str | None = None) -> EntitlementResponse:
        payload = {
            "schema": "proofsignal.entitlement-token-request/v1",
            "schemaVersion": 1,
            "email": email,
            "client": {
                "cliVersion": self.config.cliVersion,
                "platform": self.config.platform,
                "integration": integration,
            },
        }
        status, data, transport_blocker = self._json_request("POST", "/entitlements/request-token", payload=payload)
        if transport_blocker:
            return EntitlementResponse(data={}, blocker=transport_blocker)
        if status != 200:
            return EntitlementResponse(data={}, blocker=_http_blocker(status, data, delivery=True))
        blocker = _validate_token_delivery(data, production=self.config.apiBaseUrl == DEFAULT_API_BASE_URL)
        return EntitlementResponse(data=data, blocker=blocker)

    def exchange_token(self, token: str) -> TokenExchangeResponse:
        payload = {
            "schema": "proofsignal.entitlement-exchange-request/v1",
            "schemaVersion": 1,
            "token": token,
            "client": {
                "cliVersion": self.config.cliVersion,
                "platform": self.config.platform,
            },
        }
        status, data, transport_blocker = self._json_request("POST", "/entitlements/exchange", payload=payload)
        if transport_blocker:
            return TokenExchangeResponse(data={}, blocker=transport_blocker)
        if status != 200:
            return TokenExchangeResponse(data={}, blocker=_http_blocker(status, data, exchange=True))
        blocker = _validate_exchange(data, production=self.config.apiBaseUrl == DEFAULT_API_BASE_URL)
        if blocker:
            return TokenExchangeResponse(data=data, blocker=blocker)
        receipt = RuntimeEntitlementReceipt.from_dict(data)
        return TokenExchangeResponse(receipt=receipt, data=data)

    def _json_request(self, method: str, path: str, *, payload: dict[str, Any] | None = None, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], RuntimeSetupBlocker | None]:
        url = f"{self.config.apiBaseUrl}{path}"
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            url,
            data=body,
            method=method,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Cache-Control": "no-store",
                **(headers or {}),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeoutSeconds) as response:  # nosec B310 - official/explicit API URL
                data = _parse_json_response(response.read())
                return response.status, data, None
        except urllib.error.HTTPError as exc:
            return exc.code, _parse_json_response(exc.read()), None
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            return 0, {}, RuntimeSetupBlocker(code="api.unavailable", message="ProofSignal entitlement API is unavailable.")


def _validate_api_base_url(value: str) -> None:
    parsed = urllib.parse.urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("ProofSignal API base URL must be an http(s) URL.")
    if parsed.username or parsed.password or parsed.query:
        raise ValueError("ProofSignal API base URL must not contain credentials or query secrets.")


def _parse_json_response(raw: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _validate_token_delivery(data: dict[str, Any], *, production: bool) -> RuntimeSetupBlocker | None:
    policy = data.get("tokenPolicy") if isinstance(data.get("tokenPolicy"), dict) else {}
    if data.get("schema") != "proofsignal.entitlement-token-delivery/v1" or data.get("schemaVersion") != 1 or data.get("status") != "accepted":
        return RuntimeSetupBlocker(code="api.incompatible", message="Entitlement token delivery response did not match the public contract.")
    if production and (policy.get("maxExchanges") != 1 or policy.get("maxExchangesPerHour") != 1 or policy.get("defaultTokenTtlDays") != 30):
        return RuntimeSetupBlocker(code="api.incompatible", message="Production entitlement token policy did not match the public/free contract.")
    return None


def _validate_exchange(data: dict[str, Any], *, production: bool) -> RuntimeSetupBlocker | None:
    summary = data.get("receiptSummary") if isinstance(data.get("receiptSummary"), dict) else {}
    token_policy = summary.get("tokenPolicy") if isinstance(summary.get("tokenPolicy"), dict) else {}
    use_policy = summary.get("usePolicy") if isinstance(summary.get("usePolicy"), dict) else {}
    if data.get("schema") != "proofsignal.entitlement-exchange/v1" or data.get("schemaVersion") != 1:
        return RuntimeSetupBlocker(code="api.incompatible", message="Entitlement exchange response did not match the public contract.")
    if not isinstance(data.get("receipt"), str) or not data.get("receipt") or not summary.get("receiptId"):
        return RuntimeSetupBlocker(code="entitlement.malformed", message="Entitlement exchange did not include a usable receipt.")
    if production and summary.get("issuer") != PRODUCTION_RECEIPT_ISSUER:
        return RuntimeSetupBlocker(code="entitlement.rejected", message="Production entitlement receipt issuer is not trusted.")
    if use_policy.get("policyId") != "public-free":
        return RuntimeSetupBlocker(code="api.incompatible", message="Entitlement receipt use policy did not match the expected public/free contract.")
    if token_policy.get("maxExchanges") != 1 or token_policy.get("maxExchangesPerHour") != 1:
        return RuntimeSetupBlocker(code="api.incompatible", message="Entitlement exchange policy did not expose the expected exchange limits.")
    return None


def _http_blocker(status: int, data: dict[str, Any], *, delivery: bool = False, exchange: bool = False) -> RuntimeSetupBlocker:
    code = str(data.get("code") or "")
    if status in {500, 503}:
        mapped = "entitlement.delivery-unavailable" if delivery and status == 503 else "api.unavailable"
    elif status == 429:
        mapped = "entitlement.delivery-throttled" if delivery else "entitlement.exchange-throttled"
    elif exchange and status == 401:
        mapped = "entitlement.invalid-token"
    elif exchange and status == 403:
        mapped = code if code in {"entitlement.expired-token", "entitlement.exchange-limit", "entitlement.exchange-throttled", "entitlement.rejected"} else "entitlement.rejected"
    elif status == 400:
        mapped = "api.incompatible"
    else:
        mapped = code if code else "api.unavailable"
    return RuntimeSetupBlocker(code=mapped, message=_safe_failure_message(mapped))


def _safe_failure_message(code: str) -> str:
    messages = {
        "api.unavailable": "ProofSignal entitlement API is unavailable.",
        "api.incompatible": "ProofSignal entitlement API response is incompatible with this CLI.",
        "entitlement.delivery-unavailable": "ProofSignal could not send an unlock token right now.",
        "entitlement.delivery-throttled": "Unlock token delivery is temporarily throttled.",
        "entitlement.invalid-token": "The unlock token was rejected.",
        "entitlement.expired-token": "The unlock token has expired.",
        "entitlement.exchange-limit": "The unlock token exchange limit has been reached.",
        "entitlement.exchange-throttled": "Unlock token exchange is temporarily throttled.",
        "entitlement.rejected": "The entitlement request was rejected.",
        "entitlement.malformed": "The entitlement receipt is malformed.",
    }
    return messages.get(code, "ProofSignal runtime entitlement is blocked.")


def _is_expired(value: str | None) -> bool:
    if not value:
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    return parsed <= datetime.now(UTC)
