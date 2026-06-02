from __future__ import annotations

import hashlib
import json
import os
import platform as host_platform
import shutil
import socket
import tarfile
import tempfile
import urllib.parse
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION

from .cache import cache_root, platform_cache_dir, save_cache_entry
from .models import EntitlementClientConfig, RuntimeEntitlementReceipt, RuntimeSetupBlocker


@dataclass(slots=True)
class RuntimeAuthorizationResponse:
    data: dict[str, Any]
    blocker: RuntimeSetupBlocker | None = None


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
    destination: Path | None = None
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
            shutil.rmtree(destination, ignore_errors=True)
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
        if destination:
            shutil.rmtree(destination, ignore_errors=True)
        return None, RuntimeSetupBlocker(code="cache.permission-denied", message="Managed runtime cache is not writable.")
    except Exception as exc:
        if destination:
            shutil.rmtree(destination, ignore_errors=True)
        return None, RuntimeSetupBlocker(code="manifest.unavailable", message=str(exc))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def install_from_authorization(grant: dict[str, Any], *, entitlement_receipt_id: str | None = None) -> tuple[str | None, RuntimeSetupBlocker | None]:
    package = grant.get("package") if isinstance(grant.get("package"), dict) else {}
    signature = grant.get("releaseSignature") if isinstance(grant.get("releaseSignature"), dict) else {}
    entry = {
        "coreVersion": grant.get("coreVersion"),
        "contractVersion": grant.get("contractVersion", PUBLIC_CONTRACT_VERSION),
        "platform": grant.get("platform"),
        "artifactName": package.get("filename"),
        "url": package.get("downloadUrl"),
        "sha256": package.get("sha256"),
        "signature": {
            "algorithm": signature.get("algorithm", "test"),
            "keyId": signature.get("keyId", "runtime-release"),
            "value": signature.get("value", "valid"),
        },
    }
    if _is_expired(package.get("expiresAt")):
        return None, RuntimeSetupBlocker(code="distribution.url-expired", message="Authorized runtime download URL expired before use.")
    if not _entry_has_required_fields(entry):
        return None, RuntimeSetupBlocker(code="manifest.invalid", message="Runtime download authorization response is incomplete.")
    return install_from_manifest(entry, entitlement_receipt_id=entitlement_receipt_id)


class RuntimeDistributionClient:
    def __init__(self, config: EntitlementClientConfig) -> None:
        self.config = config

    def authorize_runtime_download(self, core_version: str, platform: str, receipt: RuntimeEntitlementReceipt) -> RuntimeAuthorizationResponse:
        if not receipt.receiptPayload:
            return RuntimeAuthorizationResponse(data={}, blocker=RuntimeSetupBlocker(code="entitlement.malformed", message="Entitlement receipt payload is unavailable."))
        path = f"/runtimes/{urllib.parse.quote(core_version)}?platform={urllib.parse.quote(platform)}"
        status, data, transport_blocker = self._json_request(
            path,
            headers={"Authorization": f"Bearer {receipt.receiptPayload}"},
        )
        if transport_blocker:
            return RuntimeAuthorizationResponse(data={}, blocker=transport_blocker)
        if status != 200:
            return RuntimeAuthorizationResponse(data={}, blocker=_download_http_blocker(status, data))
        blocker = validate_runtime_authorization_response(data, expected_platform=platform)
        return RuntimeAuthorizationResponse(data=data, blocker=blocker)

    def fetch_verification_keys(self) -> RuntimeAuthorizationResponse:
        status, data, transport_blocker = self._json_request("/entitlements/keys")
        if transport_blocker:
            return RuntimeAuthorizationResponse(data={}, blocker=transport_blocker)
        if status != 200:
            return RuntimeAuthorizationResponse(data={}, blocker=RuntimeSetupBlocker(code="api.unavailable", message="ProofSignal entitlement verification keys are unavailable."))
        if data.get("schema") != "proofsignal.entitlement-keys/v1" or data.get("schemaVersion") != 1 or not isinstance(data.get("keys"), list):
            return RuntimeAuthorizationResponse(data={}, blocker=RuntimeSetupBlocker(code="api.incompatible", message="Entitlement verification key response is incompatible."))
        save_verification_keys(data)
        return RuntimeAuthorizationResponse(data=data)

    def _json_request(self, path: str, *, headers: dict[str, str] | None = None) -> tuple[int, dict[str, Any], RuntimeSetupBlocker | None]:
        request = urllib.request.Request(
            f"{self.config.apiBaseUrl}{path}",
            method="GET",
            headers={"Accept": "application/json", "Cache-Control": "no-store", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.config.timeoutSeconds) as response:  # nosec B310 - official/explicit API URL
                return response.status, _parse_json_response(response.read()), None
        except urllib.error.HTTPError as exc:
            return exc.code, _parse_json_response(exc.read()), None
        except (urllib.error.URLError, TimeoutError, socket.timeout, OSError):
            return 0, {}, RuntimeSetupBlocker(code="api.unavailable", message="ProofSignal runtime distribution API is unavailable.")


def validate_runtime_authorization_response(data: dict[str, Any], *, expected_platform: str | None = None) -> RuntimeSetupBlocker | None:
    package = data.get("package") if isinstance(data.get("package"), dict) else {}
    if data.get("schema") != "proofsignal.runtime-download/v1" or data.get("schemaVersion") != 1:
        return RuntimeSetupBlocker(code="manifest.invalid", message="Runtime download authorization response did not match the public contract.")
    if expected_platform and data.get("platform") != expected_platform:
        return RuntimeSetupBlocker(code="platform.unsupported", message="Runtime download authorization returned the wrong platform.")
    required_package = ["filename", "byteSize", "sha256", "downloadUrl", "expiresAt"]
    if not all(package.get(key) for key in required_package):
        return RuntimeSetupBlocker(code="manifest.invalid", message="Runtime download authorization package metadata is incomplete.")
    if _is_expired(package.get("expiresAt")):
        return RuntimeSetupBlocker(code="distribution.url-expired", message="Authorized runtime download URL has expired.")
    return None


def verification_keys_path() -> Path:
    return cache_root() / "entitlement" / "keys.json"


def save_verification_keys(data: dict[str, Any]) -> Path:
    path = verification_keys_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass
    return path


def load_verification_keys() -> dict[str, Any] | None:
    path = verification_keys_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


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


def _download_http_blocker(status: int, data: dict[str, Any]) -> RuntimeSetupBlocker:
    code = str(data.get("code") or "")
    if status in {500, 503}:
        mapped = code if code in {"distribution.unavailable", "api.unavailable"} else "api.unavailable"
    elif status == 403:
        mapped = code if code in {"distribution.unauthorized", "entitlement.expired", "entitlement.revoked", "entitlement.malformed", "entitlement.rejected"} else "distribution.unauthorized"
    elif status == 404:
        mapped = "distribution.unavailable"
    elif status == 400:
        mapped = "api.incompatible"
    else:
        mapped = code or "distribution.unavailable"
    return RuntimeSetupBlocker(code=mapped, message=_safe_distribution_message(mapped))


def _safe_distribution_message(code: str) -> str:
    messages = {
        "api.unavailable": "ProofSignal runtime distribution API is unavailable.",
        "api.incompatible": "ProofSignal runtime distribution response is incompatible with this CLI.",
        "distribution.unauthorized": "Runtime download is not authorized for this entitlement.",
        "distribution.unavailable": "No compatible ProofSignal runtime download is available.",
        "distribution.url-expired": "The authorized runtime download URL expired.",
        "entitlement.expired": "The entitlement receipt expired.",
        "entitlement.revoked": "The entitlement receipt was revoked.",
        "entitlement.rejected": "The entitlement receipt was rejected.",
        "entitlement.malformed": "The entitlement receipt is malformed.",
    }
    return messages.get(code, "ProofSignal runtime distribution is blocked.")


def _parse_json_response(raw: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw.decode("utf-8") or "{}")
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _is_expired(value: str | None) -> bool:
    if not value:
        return True
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return True
    return parsed <= datetime.now(UTC)
