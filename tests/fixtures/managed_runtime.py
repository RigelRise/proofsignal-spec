from __future__ import annotations

import hashlib
import json
import stat
import sys
import tarfile
from pathlib import Path

from helpers import FAKE_CORE


def write_fake_core_executable(path: Path, *, mode: str = "ok") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "import os, runpy, sys",
                f"os.environ['FAKE_PROOFSIGNAL_MODE'] = {mode!r}",
                f"sys.argv = [{str(FAKE_CORE)!r}, *sys.argv[1:]]",
                f"runpy.run_path({str(FAKE_CORE)!r}, run_name='__main__')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    path.chmod(path.stat().st_mode | stat.S_IXUSR)
    return path


def build_managed_runtime_distribution(root: Path, *, platform: str, core_version: str = "0.12.0", mode: str = "ok") -> dict[str, Path | str]:
    dist = root / "dist"
    staging = root / "staging"
    dist.mkdir(parents=True, exist_ok=True)
    staging.mkdir(parents=True, exist_ok=True)
    core = write_fake_core_executable(staging / "proofsignal-core", mode=mode)
    artifact = dist / f"proofsignal-core-{platform}.tar.gz"
    with tarfile.open(artifact, "w:gz") as archive:
        archive.add(core, arcname="proofsignal-core")
    sha256 = hashlib.sha256(artifact.read_bytes()).hexdigest()
    manifest = {
        "entries": [
            {
                "coreVersion": core_version,
                "contractVersion": "proofsignal-public-cli-json/v1",
                "platform": platform,
                "artifactName": artifact.name,
                "url": artifact.as_uri(),
                "sha256": sha256,
                "signature": {"algorithm": "test", "keyId": "test-release-key", "value": "valid"},
            }
        ]
    }
    manifest_path = dist / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "artifact": artifact,
        "sha256": sha256,
        "coreVersion": core_version,
        "platform": platform,
    }

