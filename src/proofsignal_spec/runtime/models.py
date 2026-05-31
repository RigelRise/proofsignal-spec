from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION, REQUIRED_OPERATION_METADATA

MANAGED_RUNTIME_READINESS_SCHEMA = "proofsignal-spec-managed-runtime-readiness/v1"

RuntimeSource = Literal["explicit", "workspace", "env", "path", "ancestor-sibling", "managed-cache", "managed-download", "none"]
RuntimeStatus = Literal["ready", "blocked", "incompatible", "error"]
RuntimeAttemptStatus = Literal["skipped", "missing", "available", "compatible", "incompatible", "blocked", "error"]

REQUIRED_RUNTIME_BLOCKER_CODES = {
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
    "core.missing",
    "core.incompatible",
    "distribution.unavailable",
}

BLOCKER_CATEGORY_BY_PREFIX = {
    "network.": "environment",
    "manifest.": "distribution",
    "platform.": "distribution",
    "artifact.": "security",
    "cache.": "environment",
    "credentials.": "distribution",
    "entitlement.": "entitlement",
    "distribution.": "distribution",
}

SECRET_KEY_MARKERS = (
    "token",
    "secret",
    "password",
    "credential",
    "signedurl",
    "signed_url",
    "authorization",
    "bearer",
    "cookie",
    "screenshot",
    "browserstorage",
    "browser_storage",
    "localstorage",
    "sessionstorage",
    "sourcecode",
    "source_code",
    "private_runtime",
)
SECRET_VALUE_MARKERS = (
    "x-amz-signature=",
    "signature=",
    "token=",
    "access_key=",
    "password=",
    "bearer ",
    "raw-email-token",
    "email-token",
)


def clean(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: clean(v) for k, v in value.items() if v is not None}
    if isinstance(value, list):
        return [clean(v) for v in value]
    return value


def blocker_category(code: str) -> str:
    if code == "core.missing":
        return "environment"
    if code.startswith("core."):
        return "compatibility"
    for prefix, category in BLOCKER_CATEGORY_BY_PREFIX.items():
        if code.startswith(prefix):
            return category
    return "environment"


def redact_runtime_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        lower = value.lower()
        if any(marker in lower for marker in SECRET_VALUE_MARKERS):
            return "[redacted]"
        if re.search(r"https?://\S+\?\S*(sig|signature|token|credential|x-amz-)", lower):
            return "[redacted]"
        return value
    if isinstance(value, dict):
        return redact_runtime_payload(value)
    if isinstance(value, list):
        return [redact_runtime_value(item) for item in value]
    return value


def redact_runtime_payload(payload: dict[str, Any]) -> dict[str, Any]:
    redacted: dict[str, Any] = {}
    for key, value in payload.items():
        normalized = str(key).replace("-", "").replace("_", "").lower()
        if any(marker.replace("_", "") in normalized for marker in SECRET_KEY_MARKERS):
            redacted[key] = "[redacted]"
        else:
            redacted[key] = redact_runtime_value(value)
    return redacted


@dataclass(slots=True)
class RuntimeSetupBlocker:
    code: str
    message: str
    severity: Literal["blocker"] = "blocker"
    category: str | None = None
    recoveryCommand: str | None = None
    repairable: bool = False
    documentationRef: str | None = None

    def __post_init__(self) -> None:
        if self.category is None:
            self.category = blocker_category(self.code)
        if self.recoveryCommand is None:
            self.recoveryCommand = "proofsignal core setup --core-cmd <path>"

    def to_dict(self) -> dict[str, Any]:
        return redact_runtime_payload(clean(asdict(self)))


@dataclass(slots=True)
class RuntimeSourceAttempt:
    source: RuntimeSource
    status: RuntimeAttemptStatus
    terminal: bool = False
    command: str | None = None
    platform: str | None = None
    runtimeVersion: str | None = None
    contractVersion: str | None = None
    message: str = ""
    blockerCode: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return redact_runtime_payload(clean(asdict(self)))


@dataclass(slots=True)
class RuntimeEntitlementStatus:
    status: Literal["valid", "required", "expired", "revoked", "rejected", "malformed", "unverifiable", "not-required", "not-checked"] = "not-checked"
    receiptId: str | None = None
    expiresAt: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return redact_runtime_payload(clean(asdict(self)))


@dataclass(slots=True)
class RuntimeCacheStatus:
    status: Literal["hit", "miss", "corrupt", "incompatible", "not-checked"] = "not-checked"
    platform: str | None = None
    coreVersion: str | None = None
    message: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return redact_runtime_payload(clean(asdict(self)))


@dataclass(slots=True)
class RuntimeCacheEntry:
    coreVersion: str
    contractVersion: str
    platform: str
    runtimeCommand: str
    cachePath: str
    sha256: str
    verifiedAt: str
    lastUsedAt: str
    source: str = "managed-download"
    verificationStatus: str = "verified"
    entitlementReceiptId: str | None = None
    metadataPath: Any | None = field(default=None, repr=False, compare=False)

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, metadata_path: Any | None = None) -> "RuntimeCacheEntry":
        return cls(
            coreVersion=str(data.get("coreVersion", "")),
            contractVersion=str(data.get("contractVersion", PUBLIC_CONTRACT_VERSION)),
            platform=str(data.get("platform", "")),
            runtimeCommand=str(data.get("runtimeCommand", "")),
            cachePath=str(data.get("cachePath", "")),
            sha256=str(data.get("sha256", "")),
            verifiedAt=str(data.get("verifiedAt", "")),
            lastUsedAt=str(data.get("lastUsedAt", "")),
            source=str(data.get("source", "managed-download")),
            verificationStatus=str(data.get("verificationStatus", "verified")),
            entitlementReceiptId=data.get("entitlementReceiptId"),
            metadataPath=metadata_path,
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("metadataPath", None)
        return redact_runtime_payload(clean(data))


@dataclass(slots=True)
class RuntimeEntitlementReceipt:
    receiptId: str
    status: str
    issuedAt: str | None = None
    expiresAt: str | None = None
    scope: list[str] = field(default_factory=list)
    signatureStatus: str = "verified"

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RuntimeEntitlementReceipt":
        return cls(
            receiptId=str(data.get("receiptId", "")),
            status=str(data.get("status", "malformed")),
            issuedAt=data.get("issuedAt"),
            expiresAt=data.get("expiresAt"),
            scope=[str(item) for item in data.get("scope", [])],
            signatureStatus=str(data.get("signatureStatus", "not-checked")),
        )

    def to_dict(self) -> dict[str, Any]:
        return redact_runtime_payload(clean(asdict(self)))


@dataclass(slots=True)
class MetadataConsentDecision:
    status: Literal["granted", "declined", "not-asked"] = "not-asked"
    decidedAt: str | None = None
    summaryId: str | None = None
    categories: list[str] = field(default_factory=list)
    blocksRuntimeUnlock: bool = False

    def to_dict(self) -> dict[str, Any]:
        return redact_runtime_payload(clean(asdict(self)))


@dataclass(slots=True)
class ManagedRuntimeReadinessResult:
    status: RuntimeStatus
    source: RuntimeSource = "none"
    runtimeCommand: str | None = None
    runtimeVersion: str | None = None
    contractVersion: str | None = PUBLIC_CONTRACT_VERSION
    missingOperations: list[str] = field(default_factory=list)
    incompatibleOperations: list[dict[str, Any]] = field(default_factory=list)
    attempts: list[RuntimeSourceAttempt] = field(default_factory=list)
    entitlement: RuntimeEntitlementStatus = field(default_factory=RuntimeEntitlementStatus)
    cache: RuntimeCacheStatus = field(default_factory=RuntimeCacheStatus)
    blockers: list[RuntimeSetupBlocker] = field(default_factory=list)
    message: str = ""
    nextAction: str = "Continue with validation or run."
    schemaVersion: str = MANAGED_RUNTIME_READINESS_SCHEMA

    @classmethod
    def blocked(
        cls,
        blocker: RuntimeSetupBlocker,
        *,
        attempts: list[RuntimeSourceAttempt] | None = None,
        entitlement: RuntimeEntitlementStatus | None = None,
        cache: RuntimeCacheStatus | None = None,
        message: str | None = None,
    ) -> "ManagedRuntimeReadinessResult":
        return cls(
            status="blocked",
            source="none",
            attempts=attempts or [],
            entitlement=entitlement or RuntimeEntitlementStatus(),
            cache=cache or RuntimeCacheStatus(),
            blockers=[blocker],
            message=message or blocker.message,
            nextAction=blocker.recoveryCommand or "Resolve runtime setup blocker.",
        )

    def to_dict(self) -> dict[str, Any]:
        data = {
            "schemaVersion": self.schemaVersion,
            "status": self.status,
            "source": self.source,
            "runtimeCommand": redact_runtime_value(self.runtimeCommand),
            "runtimeVersion": self.runtimeVersion,
            "contractVersion": self.contractVersion,
            "requiredOperations": REQUIRED_OPERATION_METADATA,
            "requiredOperationsByName": {item["operationName"]: item for item in REQUIRED_OPERATION_METADATA},
            "missingOperations": self.missingOperations,
            "incompatibleOperations": self.incompatibleOperations,
            "attempts": [item.to_dict() for item in self.attempts],
            "entitlement": self.entitlement.to_dict(),
            "cache": self.cache.to_dict(),
            "blockers": [item.to_dict() for item in self.blockers],
            "message": self.message,
            "nextAction": self.nextAction,
        }
        return redact_runtime_payload(clean(data))
