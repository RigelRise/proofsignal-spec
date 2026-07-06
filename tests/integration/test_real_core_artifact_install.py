"""Install a real Core-built runtime package through the managed installer.

Cross-repo guard: each repo's own tests exercise its own fixture layout, so a
divergence between Core's packaged archive layout and this installer would ship
silently. This test consumes an actual artifact from the sibling Core repo
(``../proofsignal/dist/runtime``) when one exists and skips cleanly otherwise.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

from proofsignal_spec.core.adapter import CoreAdapter
from proofsignal_spec.core.contracts import PUBLIC_CONTRACT_VERSION
from proofsignal_spec.runtime.distribution import install_from_manifest, normalize_platform


def _discover_real_artifact() -> Path | None:
    override = os.environ.get("PROOFSIGNAL_REAL_CORE_ARTIFACT")
    if override:
        path = Path(override).expanduser()
        return path if path.is_file() else None
    platform = normalize_platform()
    if platform is None:
        return None
    dist_dir = Path(__file__).resolve().parents[2].parent / "proofsignal" / "dist" / "runtime"
    if not dist_dir.is_dir():
        return None
    candidates: list[tuple[tuple[int, int, int], Path]] = []
    for artifact in dist_dir.glob(f"proofsignal-core-*-{platform}.tar.gz"):
        match = re.match(r"proofsignal-core-(\d+)\.(\d+)\.(\d+)-", artifact.name)
        if match:
            candidates.append((tuple(int(part) for part in match.groups()), artifact))
    if not candidates:
        return None
    return max(candidates)[1]


REAL_ARTIFACT = _discover_real_artifact()


def _artifact_version(artifact: Path) -> str:
    match = re.match(r"proofsignal-core-(\d+\.\d+\.\d+)-", artifact.name)
    assert match is not None
    return match.group(1)


@pytest.mark.skipif(REAL_ARTIFACT is None, reason="no real Core runtime artifact available")
@pytest.mark.skipif(shutil.which("node") is None, reason="node is required to run the packaged runtime")
def test_real_core_artifact_installs_and_serves_the_public_contract(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert REAL_ARTIFACT is not None
    monkeypatch.setenv("PROOFSIGNAL_RUNTIME_CACHE_DIR", str(tmp_path / "cache"))
    platform = normalize_platform()
    core_version = _artifact_version(REAL_ARTIFACT)
    entry = {
        "coreVersion": core_version,
        "contractVersion": PUBLIC_CONTRACT_VERSION,
        "platform": platform,
        "artifactName": REAL_ARTIFACT.name,
        "url": REAL_ARTIFACT.as_uri(),
        "sha256": hashlib.sha256(REAL_ARTIFACT.read_bytes()).hexdigest(),
        "signature": {"algorithm": "ed25519", "keyId": "local-real-artifact", "value": "local"},
    }

    command, blocker = install_from_manifest(entry)

    assert blocker is None
    assert command is not None
    assert command.endswith("proofsignal-core/bin/proofsignal-core")
    assert os.access(command, os.X_OK)

    compat = CoreAdapter(executable=command, cwd=tmp_path).check_compatibility()
    assert compat.compatible
    assert compat.contractVersion == PUBLIC_CONTRACT_VERSION
    assert compat.proofsignalVersion == core_version

    raw = subprocess.run(
        [command, "version", "--json"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=120,
        check=True,
    )
    envelope = json.loads(raw.stdout)
    assert envelope["schema"] == "proofsignal.version/v1"
