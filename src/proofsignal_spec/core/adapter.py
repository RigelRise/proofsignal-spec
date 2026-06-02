from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any

from .contracts import CompatibilityResult, normalize_status, validate_version_response
from .errors import CoreExecutionError, CoreIncompatibleError, CoreMissingError

CORE_SETUP_HINT = (
    "Run `proofsignal core setup --json` to discover and persist an existing "
    "ProofSignal Core command, or pass `--core-cmd /path/to/proofsignal` for a "
    "one-off command."
)


class CoreAdapter:
    def __init__(self, executable: str | None = None, cwd: Path | None = None) -> None:
        self.executable = executable or os.environ.get("PROOFSIGNAL_CORE_CMD", "proofsignal")
        self.cwd = cwd

    def _base_command(self) -> list[str]:
        raw = self.executable.strip()
        path = Path(raw).expanduser()
        if path.exists() and path.is_dir():
            if (path / "package.json").exists():
                return ["npm", "--silent", "--prefix", str(path.resolve()), "run", "proofsignal:dev", "--"]
            raise CoreMissingError(f"ProofSignal Core path is a directory without package.json: {path}. {CORE_SETUP_HINT}")
        if path.exists() and path.is_file():
            return [str(path.resolve())]

        parts = shlex.split(raw)
        if len(parts) > 1:
            resolved = shutil.which(parts[0])
            if not resolved:
                raise CoreMissingError(f"ProofSignal Core command not found: {parts[0]}. {CORE_SETUP_HINT}")
            return [resolved, *parts[1:]]

        resolved = shutil.which(raw)
        if not resolved:
            raise CoreMissingError(f"ProofSignal Core executable not found: {self.executable}. {CORE_SETUP_HINT}")
        return [resolved]

    def _run(self, args: list[str], env: dict[str, str] | None = None) -> dict[str, Any]:
        base_command = self._base_command()
        proc = subprocess.run(
            [*base_command, *args],
            cwd=str(self.cwd) if self.cwd else None,
            env={**os.environ, **(env or {})},
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if proc.returncode != 0 and not proc.stdout.strip():
            raise CoreExecutionError(proc.stderr.strip() or f"ProofSignal Core exited with {proc.returncode}")
        try:
            return json.loads(proc.stdout)
        except json.JSONDecodeError as exc:
            start = proc.stdout.find("{")
            end = proc.stdout.rfind("}")
            if start != -1 and end > start:
                try:
                    return json.loads(proc.stdout[start : end + 1])
                except json.JSONDecodeError:
                    pass
            raise CoreExecutionError(f"ProofSignal Core returned non-JSON output: {proc.stdout[:200]}") from exc

    def version(self) -> dict[str, Any]:
        return self._run(["version", "--json"])

    def check_compatibility(self) -> CompatibilityResult:
        return validate_version_response(self.version())

    def require_compatible(self) -> CompatibilityResult:
        result = self.check_compatibility()
        if not result.compatible:
            raise CoreIncompatibleError(result.message)
        return result

    def authoring_check(
        self,
        run_request: Path,
        main_skill: Path,
        skills: list[Path],
        runtime_readiness: bool = False,
        entitlement_receipt: Path | str | None = None,
    ) -> dict[str, Any]:
        self.require_compatible()
        args = ["authoring-check", "run-request", str(run_request), "--skill", str(main_skill)]
        for skill in skills:
            if skill != main_skill:
                args.extend(["--skill", str(skill)])
        if runtime_readiness:
            args.append("--runtime-readiness")
        args.append("--json")
        return self._run(args, env=_receipt_env(entitlement_receipt))

    def run(
        self,
        run_request: Path,
        main_skill: Path,
        skills: list[Path],
        output_dir: Path | None = None,
        headed: bool = False,
        slow_mo_ms: int = 0,
        env: dict[str, str] | None = None,
        entitlement_receipt: Path | str | None = None,
    ) -> dict[str, Any]:
        self.require_compatible()
        args = ["run", str(run_request), "--skill", str(main_skill)]
        for skill in skills:
            if skill != main_skill:
                args.extend(["--skill", str(skill)])
        if output_dir:
            args.extend(["--output-dir", str(output_dir)])
        if headed:
            args.append("--headed")
        if slow_mo_ms:
            args.extend(["--slow-mo", str(slow_mo_ms)])
        args.append("--json")
        return self._run(args, env={**(env or {}), **_receipt_env(entitlement_receipt)})

    def inspect_report(self, report_path: Path, entitlement_receipt: Path | str | None = None) -> dict[str, Any]:
        self.require_compatible()
        return self._run(["report", "inspect", str(report_path), "--json"], env=_receipt_env(entitlement_receipt))


def _receipt_env(entitlement_receipt: Path | str | None) -> dict[str, str]:
    env: dict[str, str] = {}
    if entitlement_receipt:
        env["PROOFSIGNAL_ENTITLEMENT_RECEIPT"] = str(entitlement_receipt)
    if not os.environ.get("PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON"):
        try:
            from proofsignal_spec.runtime.distribution import load_verification_keys

            cached = load_verification_keys()
            keys = cached.get("keys") if isinstance(cached, dict) else None
            if isinstance(keys, list):
                env["PROOFSIGNAL_ENTITLEMENT_PUBLIC_KEYS_JSON"] = json.dumps(keys, separators=(",", ":"))
        except Exception:
            pass
    return env


def readiness(executable: str | None = None, cwd: Path | None = None) -> dict[str, Any]:
    adapter = CoreAdapter(executable=executable, cwd=cwd)
    try:
        result = adapter.check_compatibility()
        return {"available": True, **result.to_dict()}
    except CoreMissingError as exc:
        return {"available": False, "compatible": False, "message": str(exc), "missingOperations": []}
    except Exception as exc:
        return {"available": True, "compatible": False, "message": str(exc), "missingOperations": []}


def core_status(result: dict[str, Any]) -> str:
    return normalize_status(result)
