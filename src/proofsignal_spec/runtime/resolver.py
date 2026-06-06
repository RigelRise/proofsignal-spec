from __future__ import annotations

import os
import shutil
from pathlib import Path

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION
from proofsignal_spec.core.errors import CoreExecutionError, CoreMissingError
from proofsignal_spec.workspace.repository import get_core_command, get_entitlement_api_base_url

from .cache import load_cache_entry, mark_cache_used
from .distribution import (
    RuntimeDistributionClient,
    install_from_authorization,
    install_from_manifest,
    load_manifest,
    manifest_entries,
    normalize_platform,
    prepare_verification_keys,
    select_manifest_entry,
)
from .entitlement import ensure_entitlement, load_receipt, resolve_entitlement_config
from .models import (
    ManagedRuntimeReadinessResult,
    RuntimeApiStatus,
    RuntimeCacheStatus,
    RuntimeEntitlementStatus,
    RuntimeVerificationKeyStatus,
    RuntimeSetupBlocker,
    RuntimeSourceAttempt,
)


def ensure_core_runtime(
    project: Path,
    *,
    explicit_core_cmd: str | None = None,
    api_base_url: str | None = None,
    email: str | None = None,
    token: str | None = None,
    integration: str | None = None,
    context: str = "runtime",
) -> ManagedRuntimeReadinessResult:
    project = project.resolve()
    config = resolve_entitlement_config(api_base_url=api_base_url, workspace_api_base_url=get_entitlement_api_base_url(project))
    api_status = RuntimeApiStatus(baseUrl=config.apiBaseUrl, source=config.source, status="not-checked")
    attempts: list[RuntimeSourceAttempt] = []
    for source, command in _override_candidates(project, explicit_core_cmd):
        attempt = _verify_command(project, source, command)
        attempts.append(attempt)
        if attempt.status == "compatible":
            entitlement, entitlement_checked_api = _override_entitlement_status(
                config,
                email=email,
                token=token,
                integration=integration,
                context=context,
            )
            if entitlement:
                if entitlement_checked_api and not (entitlement.blockerCode or "").startswith("api."):
                    api_status.status = "reachable"
                if entitlement.status != "valid":
                    code = entitlement.blockerCode or _entitlement_blocker_code(entitlement.status)
                    blocker = RuntimeSetupBlocker(
                        code=code,
                        message=entitlement.message or "Email unlock token is required before protected ProofSignal Core operations.",
                        recoveryCommand="Run `proofsignal init --here --integration codex` and enter the email unlock token, or provide a valid entitlement receipt.",
                    )
                    if code.startswith("api."):
                        api_status.status = "unreachable"
                    result = ManagedRuntimeReadinessResult.blocked(
                        blocker,
                        attempts=attempts,
                        entitlement=entitlement,
                        cache=RuntimeCacheStatus(status="not-checked"),
                        message=blocker.message,
                    )
                    result.api = api_status
                    return result
                verification_keys, key_blocker = prepare_verification_keys(config, entitlement)
                if key_blocker:
                    if key_blocker.code == "entitlement.keys-unavailable":
                        api_status.status = "unreachable"
                    result = ManagedRuntimeReadinessResult.blocked(
                        key_blocker,
                        attempts=attempts,
                        entitlement=entitlement,
                        cache=RuntimeCacheStatus(status="not-checked"),
                        verification_keys=verification_keys,
                        message=key_blocker.message,
                    )
                    result.api = api_status
                    return result
            else:
                verification_keys = RuntimeVerificationKeyStatus(status="not-required", source="not-required")
            return ManagedRuntimeReadinessResult(
                status="ready",
                source=source,  # type: ignore[arg-type]
                runtimeCommand=command,
                runtimeVersion=attempt.runtimeVersion,
                contractVersion=attempt.contractVersion or PUBLIC_CONTRACT_VERSION,
                attempts=attempts,
                api=api_status,
                entitlement=entitlement or RuntimeEntitlementStatus(status="not-required"),
                cache=RuntimeCacheStatus(status="not-checked"),
                verificationKeys=verification_keys,
                message="ProofSignal runtime is ready.",
                nextAction="Continue with validation or run.",
            )
        if attempt.terminal:
            return _blocked_from_attempt(attempt, attempts)

    platform = normalize_platform()
    if not platform:
        blocker = RuntimeSetupBlocker(code="platform.unsupported", message="This host platform is not supported by managed ProofSignal runtime distribution.")
        attempts.append(RuntimeSourceAttempt(source="managed-cache", status="skipped", terminal=False, blockerCode=blocker.code, message=blocker.message))
        result = ManagedRuntimeReadinessResult.blocked(blocker, attempts=attempts, cache=RuntimeCacheStatus(status="not-checked"), message=blocker.message)
        result.api = api_status
        return result

    entitlement = ensure_entitlement(
        config=config,
        email=email,
        token=token,
        request_delivery=context == "init",
        integration=integration,
    )
    if entitlement.status != "valid":
        code = entitlement.blockerCode or _entitlement_blocker_code(entitlement.status)
        blocker = RuntimeSetupBlocker(
            code=code,
            message=entitlement.message or "Email unlock token is required before managed runtime download.",
            recoveryCommand="Run `proofsignal init --here --integration codex` and enter the email unlock token, or use `proofsignal core setup --core-cmd <path>`.",
        )
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=blocker.message, blockerCode=code))
        api_status.status = "unreachable" if code.startswith("api.") else "reachable"
        result = ManagedRuntimeReadinessResult.blocked(
            blocker,
            attempts=attempts,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="miss", platform=platform),
        )
        result.api = api_status
        return result
    api_status.status = "reachable"
    verification_keys, key_blocker = prepare_verification_keys(config, entitlement)
    if key_blocker:
        if key_blocker.code == "entitlement.keys-unavailable":
            api_status.status = "unreachable"
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=key_blocker.message, blockerCode=key_blocker.code))
        result = ManagedRuntimeReadinessResult.blocked(
            key_blocker,
            attempts=attempts,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="miss", platform=platform),
            verification_keys=verification_keys,
        )
        result.api = api_status
        return result
    entry = load_cache_entry(platform=platform)
    if entry:
        if entry.entitlementReceiptId and entitlement.receiptId and entry.entitlementReceiptId != entitlement.receiptId:
            attempts.append(
                RuntimeSourceAttempt(
                    source="managed-cache",
                    status="blocked",
                    terminal=False,
                    command=entry.runtimeCommand,
                    platform=platform,
                    message="Cached runtime is linked to a different entitlement receipt.",
                    blockerCode="entitlement.rejected",
                )
            )
        else:
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
                    api=api_status,
                    entitlement=entitlement,
                    cache=RuntimeCacheStatus(status="hit", platform=platform, coreVersion=entry.coreVersion),
                    verificationKeys=verification_keys,
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

    manifest, manifest_blocker = load_manifest()
    if manifest_blocker and manifest_blocker.code != "distribution.unavailable":
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=manifest_blocker.message, blockerCode=manifest_blocker.code))
        result = ManagedRuntimeReadinessResult.blocked(
            manifest_blocker,
            attempts=attempts,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="miss", platform=platform),
            verification_keys=verification_keys,
        )
        result.api = api_status
        return result
    if manifest:
        try:
            selected = select_manifest_entry(manifest_entries(manifest or {}), platform=platform, contract_version=PUBLIC_CONTRACT_VERSION)
        except Exception:
            blocker = RuntimeSetupBlocker(code="manifest.invalid", message="Managed runtime manifest does not contain a compatible entry for this platform and contract.")
            attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=blocker.message, blockerCode=blocker.code))
            result = ManagedRuntimeReadinessResult.blocked(blocker, attempts=attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="miss", platform=platform))
            result.verificationKeys = verification_keys
            result.api = api_status
            return result
        runtime_core_version = str(selected.get("coreVersion"))
        runtime_command, blocker = install_from_manifest(selected, entitlement_receipt_id=entitlement.receiptId)
    else:
        receipt = load_receipt()
        if not receipt:
            blocker = RuntimeSetupBlocker(code="entitlement.malformed", message="Entitlement receipt file is unavailable after unlock.")
            attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=blocker.message, blockerCode=blocker.code))
            result = ManagedRuntimeReadinessResult.blocked(blocker, attempts=attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="miss", platform=platform))
            result.verificationKeys = verification_keys
            result.api = api_status
            return result
        distribution_client = RuntimeDistributionClient(config)
        grant = distribution_client.authorize_runtime_download(os.environ.get("PROOFSIGNAL_CORE_VERSION", "0.12.0"), platform, receipt)
        if grant.blocker:
            attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=grant.blocker.message, blockerCode=grant.blocker.code))
            result = ManagedRuntimeReadinessResult.blocked(grant.blocker, attempts=attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="miss", platform=platform), verification_keys=verification_keys)
            result.api = api_status
            return result
        runtime_core_version = str(grant.data.get("coreVersion", os.environ.get("PROOFSIGNAL_CORE_VERSION", "0.12.0")))
        runtime_command, blocker = install_from_authorization(grant.data, entitlement_receipt_id=entitlement.receiptId)
    if blocker or not runtime_command:
        actual = blocker or RuntimeSetupBlocker(code="distribution.unavailable", message="Managed runtime installation failed.")
        attempts.append(RuntimeSourceAttempt(source="managed-download", status="blocked", terminal=True, platform=platform, message=actual.message, blockerCode=actual.code))
        result = ManagedRuntimeReadinessResult.blocked(actual, attempts=attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="miss", platform=platform), verification_keys=verification_keys)
        result.api = api_status
        return result
    attempt = _verify_command(project, "managed-download", runtime_command, platform=platform)
    attempts.append(attempt)
    if attempt.status == "compatible":
        return ManagedRuntimeReadinessResult(
            status="ready",
            source="managed-download",
            runtimeCommand=runtime_command,
            runtimeVersion=attempt.runtimeVersion or runtime_core_version,
            contractVersion=attempt.contractVersion or PUBLIC_CONTRACT_VERSION,
            attempts=attempts,
            api=api_status,
            entitlement=entitlement,
            cache=RuntimeCacheStatus(status="hit", platform=platform, coreVersion=runtime_core_version),
            verificationKeys=verification_keys,
            message="ProofSignal runtime is ready.",
            nextAction="Continue with validation or run.",
        )
    result = _blocked_from_attempt(attempt, attempts, entitlement=entitlement, cache=RuntimeCacheStatus(status="incompatible", platform=platform))
    result.verificationKeys = verification_keys
    result.api = api_status
    return result


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


def _override_entitlement_status(
    config,
    *,
    email: str | None,
    token: str | None,
    integration: str | None,
    context: str,
) -> tuple[RuntimeEntitlementStatus | None, bool]:
    token_available = bool(token or os.environ.get("PROOFSIGNAL_EMAIL_UNLOCK_TOKEN"))
    email_available = bool(email or os.environ.get("PROOFSIGNAL_EMAIL"))
    receipt_available = load_receipt() is not None
    should_resolve = token_available or receipt_available or (context == "init" and email_available)
    if not should_resolve:
        return None, False
    return (
        ensure_entitlement(
            config=config,
            email=email,
            token=token,
            request_delivery=context == "init",
            integration=integration,
        ),
        token_available or (context == "init" and email_available),
    )


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
        recoveryCommand="proofsignal core setup --json" if code == "core.missing" else "proofsignal core setup --core-cmd <path>",
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
