from __future__ import annotations

import os
import shutil
from pathlib import Path

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION
from proofsignal_spec.core.errors import CoreExecutionError, CoreMissingError
from proofsignal_spec.workspace.repository import get_core_command

from .cache import load_cache_entry, mark_cache_used
from .distribution import install_from_manifest, load_manifest, manifest_entries, normalize_platform, select_manifest_entry
from .entitlement import ensure_entitlement
from .models import (
    ManagedRuntimeReadinessResult,
    RuntimeCacheStatus,
    RuntimeEntitlementStatus,
    RuntimeSetupBlocker,
    RuntimeSourceAttempt,
)


def ensure_core_runtime(
    project: Path,
    *,
    explicit_core_cmd: str | None = None,
    context: str = "runtime",
) -> ManagedRuntimeReadinessResult:
    project = project.resolve()
    attempts: list[RuntimeSourceAttempt] = []
    for source, command in _override_candidates(project, explicit_core_cmd):
        attempt = _verify_command(project, source, command)
        attempts.append(attempt)
        if attempt.status == "compatible":
            return ManagedRuntimeReadinessResult(
                status="ready",
                source=source,  # type: ignore[arg-type]
                runtimeCommand=command,
                runtimeVersion=attempt.runtimeVersion,
                contractVersion=attempt.contractVersion or PUBLIC_CONTRACT_VERSION,
                attempts=attempts,
                entitlement=RuntimeEntitlementStatus(status="not-required"),
                cache=RuntimeCacheStatus(status="not-checked"),
                message="ProofSignal runtime is ready.",
                nextAction="Continue with validation or run.",
            )
        if attempt.terminal:
            return _blocked_from_attempt(attempt, attempts)

    platform = normalize_platform()
    if not platform:
        blocker = RuntimeSetupBlocker(code="platform.unsupported", message="This host platform is not supported by managed ProofSignal runtime distribution.")
        attempts.append(RuntimeSourceAttempt(source="managed-cache", status="skipped", terminal=False, blockerCode=blocker.code, message=blocker.message))
        return ManagedRuntimeReadinessResult.blocked(blocker, attempts=attempts, cache=RuntimeCacheStatus(status="not-checked"), message=blocker.message)

    entry = load_cache_entry(platform=platform)
    if entry:
        attempt = _verify_command(project, "managed-cache", entry.runtimeCommand, platform=platform)
        attempts.append(attempt)
        if attempt.status == "compatible":
            mark_cache_used(entry)
            return ManagedRuntimeReadinessResult(
                status="ready",
                source="managed-cache",
                runtimeCommand=entry.runtimeCommand,
                runtimeVersion=attempt.runtimeVersion or entry.coreVersion,
                contractVersion=attempt.contractVersion or entry.contractVersion,
                attempts=attempts,
                entitlement=RuntimeEntitlementStatus(status="valid", receiptId=entry.entitlementReceiptId),
                cache=RuntimeCacheStatus(status="hit", platform=platform, coreVersion=entry.coreVersion),
                message="ProofSignal runtime is ready.",
                nextAction="Continue with validation or run.",
            )
        attempts[-1] = RuntimeSourceAttempt(
            source="managed-cache",
            status="incompatible",
            terminal=False,
            command=entry.runtimeCommand,
            platform=platform,
            message=attempt.message,
            blockerCode="core.incompatible",
        )

    entitlement = ensure_entitlement()
    if entitlement.status != "valid":
        code = _entitlement_blocker_code(entitlement.status)
        blocker = RuntimeSetupBlocker(
            code=code,
            message=entitlement.message or "Email unlock token is required before managed runtime download.",
            recoveryCommand="Run `proofsignal init --here --integration codex` and enter the email unlock token, or use `proofsignal core setup --core-cmd <path>`.",
        )
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=blocker.message, blockerCode=code))
        return ManagedRuntimeReadinessResult.blocked(
            blocker,
            attempts=attempts,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="miss", platform=platform),
        )

    manifest, manifest_blocker = load_manifest()
    if manifest_blocker:
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=manifest_blocker.message, blockerCode=manifest_blocker.code))
        return ManagedRuntimeReadinessResult.blocked(
            manifest_blocker,
            attempts=attempts,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="miss", platform=platform),
        )
    try:
        selected = select_manifest_entry(manifest_entries(manifest or {}), platform=platform, contract_version=PUBLIC_CONTRACT_VERSION)
    except Exception:
        blocker = RuntimeSetupBlocker(code="manifest.invalid", message="Managed runtime manifest does not contain a compatible entry for this platform and contract.")
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=blocker.message, blockerCode=blocker.code))
        return ManagedRuntimeReadinessResult.blocked(blocker, attempts=attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="miss", platform=platform))
    runtime_command, blocker = install_from_manifest(selected, entitlement_receipt_id=entitlement.receiptId)
    if blocker or not runtime_command:
        actual = blocker or RuntimeSetupBlocker(code="distribution.unavailable", message="Managed runtime installation failed.")
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=actual.message, blockerCode=actual.code))
        return ManagedRuntimeReadinessResult.blocked(actual, attempts=attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="miss", platform=platform))
    attempt = _verify_command(project, "managed-download", runtime_command, platform=platform)
    attempts.append(attempt)
    if attempt.status == "compatible":
        return ManagedRuntimeReadinessResult(
            status="ready",
            source="managed-download",
            runtimeCommand=runtime_command,
            runtimeVersion=attempt.runtimeVersion or str(selected.get("coreVersion")),
            contractVersion=attempt.contractVersion or PUBLIC_CONTRACT_VERSION,
            attempts=attempts,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="hit", platform=platform, coreVersion=str(selected.get("coreVersion"))),
            message="ProofSignal runtime is ready.",
            nextAction="Continue with validation or run.",
        )
    return _blocked_from_attempt(attempt, attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="incompatible", platform=platform, coreVersion=str(selected.get("coreVersion"))))


def _override_candidates(project: Path, explicit_core_cmd: str | None) -> list[tuple[str, str]]:
    candidates: list[tuple[str, str]] = []
    if explicit_core_cmd:
        candidates.append(("explicit", explicit_core_cmd))
    workspace_cmd = get_core_command(project)
    if workspace_cmd:
        candidates.append(("workspace", workspace_cmd))
    env_cmd = os.environ.get("PROOFSIGNAL_CORE_CMD")
    if env_cmd:
        candidates.append(("env", env_cmd))
    path_core = shutil.which("proofsignal-core")
    if path_core:
        candidates.append(("path", path_core))
    for path in _ancestor_sibling_paths(project):
        candidates.append(("ancestor-sibling", str(path)))
    return candidates


def _ancestor_sibling_paths(project: Path) -> list[Path]:
    paths: list[Path] = []
    seen: set[Path] = set()
    start = project.resolve()
    for node in [start, *start.parents]:
        sibling = (node.parent / "proofsignal").resolve()
        if sibling == start or sibling in seen:
            continue
        seen.add(sibling)
        if sibling.exists():
            paths.append(sibling)
    return paths


def _verify_command(project: Path, source: str, command: str, *, platform: str | None = None) -> RuntimeSourceAttempt:
    terminal = source in {"explicit", "workspace", "env"}
    try:
        compatibility = CoreAdapter(executable=command, cwd=project).check_compatibility()
    except CoreMissingError as exc:
        return RuntimeSourceAttempt(source=source, status="missing", terminal=terminal, command=command, platform=platform, message=str(exc), blockerCode="core.missing")
    except CoreExecutionError as exc:
        return RuntimeSourceAttempt(source=source, status="error", terminal=terminal, command=command, platform=platform, message=str(exc), blockerCode="core.incompatible")
    except Exception as exc:
        return RuntimeSourceAttempt(source=source, status="error", terminal=terminal, command=command, platform=platform, message=str(exc), blockerCode="core.incompatible")
    if compatibility.compatible:
        return RuntimeSourceAttempt(
            source=source,
            status="compatible",
            terminal=True,
            command=command,
            platform=platform,
            runtimeVersion=compatibility.proofsignalVersion,
            contractVersion=compatibility.contractVersion,
            message="Core command verified through public CLI contract.",
        )
    return RuntimeSourceAttempt(
        source=source,
        status="incompatible",
        terminal=terminal,
        command=command,
        platform=platform,
        runtimeVersion=compatibility.proofsignalVersion,
        contractVersion=compatibility.contractVersion,
        message=compatibility.message,
        blockerCode="core.incompatible",
    )


def _blocked_from_attempt(
    attempt: RuntimeSourceAttempt,
    attempts: list[RuntimeSourceAttempt],
    *,
    entitlement: RuntimeEntitlementStatus | None = None,
    cache: RuntimeCacheStatus | None = None,
) -> ManagedRuntimeReadinessResult:
    status = "incompatible" if attempt.status == "incompatible" else ("blocked" if attempt.status == "missing" else "error")
    code = "core.missing" if attempt.status == "missing" else "core.incompatible"
    blocker = RuntimeSetupBlocker(
        code=code,
        message=attempt.message or "Configured ProofSignal runtime is incompatible.",
        recoveryCommand="proofsignal-spec core setup --json" if code == "core.missing" else "proofsignal core setup --core-cmd <path>",
    )
    return ManagedRuntimeReadinessResult(
        status=status,  # type: ignore[arg-type]
        source="none",
        runtimeCommand=attempt.command,
        runtimeVersion=attempt.runtimeVersion,
        contractVersion=attempt.contractVersion or PUBLIC_CONTRACT_VERSION,
        attempts=attempts,
        entitlement=entitlement or RuntimeEntitlementStatus(status="not-checked"),
        cache=cache or RuntimeCacheStatus(status="not-checked"),
        blockers=[blocker],
        message=blocker.message,
        nextAction=blocker.recoveryCommand or "Resolve Core compatibility.",
    )


def _entitlement_blocker_code(status: str) -> str:
    mapping = {
        "required": "entitlement.unlock-required",
        "expired": "entitlement.expired",
        "revoked": "entitlement.revoked",
        "rejected": "entitlement.rejected",
        "malformed": "entitlement.rejected",
        "unverifiable": "entitlement.rejected",
    }
    return mapping.get(status, "entitlement.rejected")
