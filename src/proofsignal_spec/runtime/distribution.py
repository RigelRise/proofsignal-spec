from __future__ import annotations

import hashlib
import json
import os
import platform as host_platform
import shutil
import tarfile
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION

from .cache import platform_cache_dir, save_cache_entry
from .models import RuntimeSetupBlocker


def normalize_platform(system: str | None = None, machine: str | None = None) -> str | None:
    system = (system or host_platform.system()).lower()
    machine = (machine or host_platform.machine()).lower()
    if system == "darwin" and machine in {"arm64", "aarch64"}:
        return "darwin-arm64"
    if system == "darwin" and machine in {"x86_64", "amd64"}:
        return "darwin-x64"
    if system == "linux" and machine in {"x86_64", "amd64"}:
        return "linux-x64"
    return None


def load_manifest() -> tuple[dict[str, Any] | None, RuntimeSetupBlocker | None]:
    raw = os.environ.get("PROOFSIGNAL_RUNTIME_MANIFEST_JSON")
    if raw:
        try:
            return json.loads(raw), None
        except json.JSONDecodeError:
            return None, RuntimeSetupBlocker(code="manifest.invalid", message="Managed runtime manifest JSON is invalid.")
    path = os.environ.get("PROOFSIGNAL_RUNTIME_MANIFEST_PATH")
    if path:
        try:
            return json.loads(Path(path).expanduser().read_text(encoding="utf-8")), None
        except FileNotFoundError:
            return None, RuntimeSetupBlocker(code="manifest.unavailable", message="Managed runtime manifest path was not found.")
        except json.JSONDecodeError:
            return None, RuntimeSetupBlocker(code="manifest.invalid", message="Managed runtime manifest file is invalid.")
    return None, RuntimeSetupBlocker(
        code="distribution.unavailable",
        message="Official managed runtime distribution is not configured for this Spec build. Use an override or configure the distribution manifest.",
        recoveryCommand="proofsignal core setup --core-cmd <path>",
    )


def manifest_entries(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(manifest.get("entries"), list):
        return [item for item in manifest["entries"] if isinstance(item, dict)]
    if all(key in manifest for key in ["coreVersion", "contractVersion", "platform", "url", "sha256"]):
        return [manifest]
    return []


def select_manifest_entry(entries: list[dict[str, Any]], *, platform: str, contract_version: str = PUBLIC_CONTRACT_VERSION) -> dict[str, Any]:
    for entry in entries:
        if entry.get("platform") == platform and entry.get("contractVersion") == contract_version and _entry_has_required_fields(entry):
            return entry
    raise ValueError("No compatible managed runtime manifest entry was found.")


def _entry_has_required_fields(entry: dict[str, Any]) -> bool:
    return all(entry.get(key) for key in ["coreVersion", "contractVersion", "platform", "url", "sha256"]) and signature_contract_available(entry)


def signature_contract_available(entry: dict[str, Any]) -> bool:
    signature = entry.get("signature")
    return isinstance(signature, dict) and bool(signature.get("algorithm")) and bool(signature.get("keyId")) and bool(signature.get("value"))


def verify_sha256(path: Path, expected: str) -> bool:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest.lower() == expected.lower()


def verify_signature_metadata(entry: dict[str, Any]) -> bool:
    signature = entry.get("signature") or {}
    value = str(signature.get("value", "")).lower()
    algorithm = str(signature.get("algorithm", "")).lower()
    if not signature_contract_available(entry):
        return False
    if value in {"invalid", "bad", "failed"}:
        return False
    return algorithm in {"test", "ed25519"}


def install_from_manifest(entry: dict[str, Any], *, entitlement_receipt_id: str | None = None) -> tuple[str | None, RuntimeSetupBlocker | None]:
    temp_dir = Path(tempfile.mkdtemp(prefix="proofsignal-runtime-"))
    artifact_path = temp_dir / str(entry.get("artifactName") or "proofsignal-core.tar.gz")
    try:
        _download_artifact(str(entry["url"]), artifact_path)
        if not verify_sha256(artifact_path, str(entry["sha256"])):
            return None, RuntimeSetupBlocker(code="artifact.integrity-failed", message="Managed runtime artifact checksum did not match.")
        if not verify_signature_metadata(entry):
            return None, RuntimeSetupBlocker(code="artifact.authenticity-failed", message="Managed runtime artifact signature could not be verified.")
        core_version = str(entry["coreVersion"])
        platform = str(entry["platform"])
        destination = platform_cache_dir(core_version, platform)
        if destination.exists():
            shutil.rmtree(destination)
        destination.mkdir(parents=True, exist_ok=True)
        with tarfile.open(artifact_path, "r:gz") as archive:
            archive.extractall(destination, filter="data")
        runtime = destination / "proofsignal-core"
        if not runtime.exists():
            return None, RuntimeSetupBlocker(code="manifest.invalid", message="Managed runtime artifact does not contain proofsignal-core.")
        runtime.chmod(runtime.stat().st_mode | 0o100)
        save_cache_entry(
            core_version=core_version,
            platform=platform,
            runtime_command=str(runtime),
            contract_version=str(entry.get("contractVersion", PUBLIC_CONTRACT_VERSION)),
            sha256=str(entry.get("sha256", "")),
            entitlement_receipt_id=entitlement_receipt_id,
        )
        return str(runtime), None
    except PermissionError:
        return None, RuntimeSetupBlocker(code="cache.permission-denied", message="Managed runtime cache is not writable.")
    except Exception as exc:
        return None, RuntimeSetupBlocker(code="manifest.unavailable", message=str(exc))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def _download_artifact(url: str, destination: Path) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme == "file":
        shutil.copyfile(Path(urllib.request.url2pathname(parsed.path)), destination)
        return
    if parsed.scheme in {"http", "https"}:
        with urllib.request.urlopen(url, timeout=30) as response, destination.open("wb") as handle:  # nosec B310 - official manifest controls URL
            shutil.copyfileobj(response, handle)
        return
    source = Path(url).expanduser()
    if source.exists():
        shutil.copyfile(source, destination)
        return
    raise FileNotFoundError("Managed runtime artifact could not be downloaded.")
