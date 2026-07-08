from __future__ import annotations

import json
import os
from pathlib import Path

from verifysignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION
from verifysignal_spec.workspace.repository import now_iso

from .models import RuntimeCacheEntry


def cache_root() -> Path:
    override = os.environ.get("VERIFYSIGNAL_RUNTIME_CACHE_DIR")
    if override:
        return Path(override).expanduser().resolve()
    return (Path.home() / ".cache" / "verifysignal" / "core").resolve()


def platform_cache_dir(core_version: str, platform: str) -> Path:
    return cache_root() / core_version / platform


def metadata_path(core_version: str, platform: str) -> Path:
    return platform_cache_dir(core_version, platform) / "metadata.json"


def save_cache_entry(
    *,
    core_version: str,
    platform: str,
    runtime_command: str,
    contract_version: str = PUBLIC_CONTRACT_VERSION,
    sha256: str = "",
    entitlement_receipt_id: str | None = None,
) -> RuntimeCacheEntry:
    root = platform_cache_dir(core_version, platform)
    root.mkdir(parents=True, exist_ok=True)
    timestamp = now_iso()
    path = metadata_path(core_version, platform)
    existing = load_cache_entry(platform=platform, version=core_version)
    verified_at = existing.verifiedAt if existing else timestamp
    entry = RuntimeCacheEntry(
        coreVersion=core_version,
        contractVersion=contract_version,
        platform=platform,
        runtimeCommand=runtime_command,
        cachePath=str(root),
        sha256=sha256,
        verifiedAt=verified_at,
        lastUsedAt=timestamp,
        entitlementReceiptId=entitlement_receipt_id,
        metadataPath=path,
    )
    path.write_text(json.dumps(entry.to_dict(), indent=2), encoding="utf-8")
    return entry


def load_cache_entry(*, platform: str | None = None, version: str | None = None) -> RuntimeCacheEntry | None:
    root = cache_root()
    if not root.exists():
        return None
    candidates: list[Path] = []
    if version and platform:
        candidates = [metadata_path(version, platform)]
    elif platform:
        candidates = sorted(root.glob(f"*/{platform}/metadata.json"), reverse=True)
    else:
        candidates = sorted(root.glob("*/*/metadata.json"), reverse=True)
    for path in candidates:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            entry = RuntimeCacheEntry.from_dict(data, metadata_path=path)
            if entry.verificationStatus == "verified":
                return entry
        except Exception:
            continue
    return None


def mark_cache_used(entry: RuntimeCacheEntry) -> RuntimeCacheEntry:
    return save_cache_entry(
        core_version=entry.coreVersion,
        platform=entry.platform,
        runtime_command=entry.runtimeCommand,
        contract_version=entry.contractVersion,
        sha256=entry.sha256,
        entitlement_receipt_id=entry.entitlementReceiptId,
    )


def quarantine_cache_entry(entry: RuntimeCacheEntry) -> None:
    if not entry.metadataPath:
        return
    path = Path(entry.metadataPath)
    if path.exists():
        data = json.loads(path.read_text(encoding="utf-8"))
        data["verificationStatus"] = "corrupt"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
