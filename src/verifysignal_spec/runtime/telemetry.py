"""Fire-and-forget per-run usage beacon (run/check).

A default-on, PII-free heartbeat covered by the free-tier Terms of Use / Privacy acceptance (the
ChatGPT / VS Code / npm telemetry model), with an env opt-out. It is NON-BLOCKING and swallows ALL
errors: telemetry must never affect whether the tool works, so being offline is fine. The payload
carries only command + outcome + client (platform / cliVersion); the opaque subjectRef is read
server-side from the Bearer receipt, never sent as PII. Project metadata is NOT sent here — if it
ever is, it must honor the VERIFYSIGNAL_METADATA_CONSENT gate.
"""

from __future__ import annotations

import json
import os
import threading
import urllib.request
from typing import Any

from .entitlement import load_receipt, resolve_entitlement_config


def usage_ping_enabled() -> bool:
    # Default on; opt out with VERIFYSIGNAL_USAGE_PING in {0,false,no,off}.
    return os.environ.get("VERIFYSIGNAL_USAGE_PING", "1").strip().lower() not in {"0", "false", "no", "off"}


def ping_outcome(status: str | None) -> str:
    """Map a command status to the ping outcome enum {pass, fail, blocked, error}."""
    value = (status or "").strip().lower()
    if value in {"passed", "pass"}:
        return "pass"
    if value in {"failed", "fail"}:
        return "fail"
    if value == "blocked":
        return "blocked"
    return "error"


def send_usage_ping(
    command: str,
    outcome: str,
    *,
    api_base_url: str | None = None,
    block: bool = False,
) -> threading.Thread | None:
    """Dispatch a usage ping in a daemon thread. Returns the thread (or None if opted out).

    `block` is for tests only: await the dispatched thread deterministically.
    """
    if not usage_ping_enabled():
        return None
    try:
        config = resolve_entitlement_config(api_base_url=api_base_url)
    except Exception:
        return None
    receipt = load_receipt()
    bearer = receipt.receiptPayload if receipt and receipt.receiptPayload else None
    thread = threading.Thread(target=_post_usage, args=(config, command, outcome, bearer), daemon=True)
    thread.start()
    if block:
        thread.join(timeout=config.timeoutSeconds + 1)
    return thread


def _post_usage(config: Any, command: str, outcome: str, bearer: str | None) -> None:
    try:
        payload = {
            "schema": "verifysignal.usage-ping/v1",
            "schemaVersion": 1,
            "command": command,
            "outcome": outcome,
            "client": {"cliVersion": config.cliVersion, "platform": config.platform},
        }
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Cache-Control": "no-store",
        }
        if bearer:
            headers["Authorization"] = f"Bearer {bearer}"
        request = urllib.request.Request(
            f"{config.apiBaseUrl}/entitlements/usage",
            data=json.dumps(payload).encode("utf-8"),
            method="POST",
            headers=headers,
        )
        with urllib.request.urlopen(request, timeout=config.timeoutSeconds):  # nosec B310 - official/explicit API URL
            pass
    except Exception:
        # Fire-and-forget: telemetry must NEVER surface or block. Offline is fine.
        pass
