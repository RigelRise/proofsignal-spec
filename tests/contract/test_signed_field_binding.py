from __future__ import annotations

import base64
import hashlib
import io
import json
import tarfile
from pathlib import Path

import pytest

from tests.fixtures.release_signing import signed_manifest_entry
from verifysignal_spec.runtime.distribution import install_from_manifest, verify_release_authenticity

# CLASS RATCHET (untrusted server fields must be bound or provably inert).
#
# The managed installer receives `entry` from the DISTRIBUTION SERVER's JSON — the exact party the
# whole release-signature architecture exists because it does NOT trust. The signature is what makes
# a hostile/compromised server survivable, so every entry field that drives behaviour must either be
# bound to the signed metadata or be provably unable to influence anything.
#
# The bug this closes: `artifactName` was neither. It flowed straight into `temp_dir / artifactName`,
# and Python's `/` lets an ABSOLUTE path replace the base entirely (`Path('/tmp/x') / '/etc/passwd'`
# -> `/etc/passwd`). The download wrote there BEFORE sha256 and signature verification, so rejecting
# the release did not un-write the attacker's bytes. Aimed at ~/.zshrc it becomes code execution.
#
# Two deliberately independent fixes (this is the security slice): the scratch path no longer uses
# the field at all, AND the field is now bound to the signed metadata. The table below is the ratchet:
# every entry field must carry a ruling, so a NEW field cannot be added without one.

FIELD_RULINGS: dict[str, str] = {
    "coreVersion": "bound",  # vs signed metadata.coreVersion
    "contractVersion": "bound",  # vs signed metadata.publicContractVersion
    "sha256": "bound",  # vs signed metadata.packages[platform].sha256 (both required 64-hex)
    "artifactName": "bound",  # vs signed metadata.packages[platform].filename
    "platform": "allowlisted: selector key only — it picks WHICH signed package to compare against, "
    "and that package's signed sha256 must still match the downloaded bytes.",
    "url": "allowlisted: the signature binds the BYTES (sha256), not their origin. A hostile url can "
    "only serve bytes that fail the hash, and nothing is written outside the scratch dir.",
    "releaseMetadataBytes": "allowlisted: this IS the signed payload — it cannot be bound to itself.",
    "signature": "allowlisted: the detached signature over releaseMetadataBytes, verified against the "
    "trusted release keys. Its own wrapper fields are attacker-mutable by design.",
}


# THE OTHER HALF OF THE SAME CLASS. The table above rules every field the untrusted SERVER sends.
# This one rules every field CORE SIGNS — because a signed field that no consumer compares is inert:
# the signature then proves only that some document was signed, not that this install matches it.
#
# Enumerated from the real Core-signed golden, so a field Core starts signing shows up here with no
# ruling and fails, rather than being quietly ignored for a release cycle.
METADATA_RULINGS: dict[str, str] = {
    "schema": "bound",  # verify_release_authenticity refuses anything that is not a runtime-release/v1
    "coreVersion": "bound",  # vs entry.coreVersion
    "publicContractVersion": "bound",  # vs entry.contractVersion
    "packages[].sha256": "bound",  # vs entry.sha256, both required 64-hex
    "packages[].filename": "bound",  # vs entry.artifactName
    "packages[].platform": "bound",  # selects WHICH signed package the bindings above compare against
    "schemaVersion": "allowlisted: `schema` already pins the document kind; the version is advisory "
    "and Core has never emitted anything but 1. Bind it the moment a v2 exists.",
    "releaseId": "allowlisted: a display label. coreVersion is the identity the install binds.",
    "generatedAt": "allowlisted: provenance metadata. Nothing schedules or expires on it, and binding "
    "a timestamp would make a signed release expire for reasons the signature cannot express.",
    "signing": "allowlisted: describes the signature we ALREADY verified to get here — mode, algorithm "
    "and keyId. Trusting it to decide how to verify would be circular.",
    "contractExamples": "allowlisted: documentation pointers into the Core repo. Not consulted by the "
    "installer, and they name paths that do not exist in an installed runtime.",
    "packages[].packageId": "allowlisted: derived from coreVersion+platform, both of which are bound.",
    "packages[].coreVersion": "allowlisted: duplicates the top-level coreVersion, which is bound.",
    "packages[].publicContractVersion": "allowlisted: duplicates the top-level one, which is bound.",
    "packages[].byteSize": "allowlisted: sha256 binds the bytes far more tightly than their count — a "
    "size match cannot make a wrong archive right, and a size mismatch cannot make a right one wrong.",
    "packages[].executable": "allowlisted: the installer reads the executable path from the extracted "
    "manifest.json, whose own bytes are bound by packages[].manifestSha256.",
    "packages[].manifestSha256": "allowlisted: the archive sha256 already covers the manifest inside it.",
    "packages[].signingKeyId": "allowlisted: duplicates the detached signature's keyId, which is the one "
    "actually used to verify. Reading it from the payload to choose a key would be circular.",
    "channel": "allowlisted: there is nothing to bind it TO. The installer has no channel expectation "
    "to be incompatible with — it installs the coreVersion it was asked for, and WHICH channels are "
    "discoverable is decided server-side by findLatestRuntimeRelease. Trust comes from the KEY: a "
    "dev-channel artifact is signed by the test key, which trusted_release_keys() admits only under "
    "VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS=1. Bind this the day the installer takes a --channel.",
    "issuer": "allowlisted: release trust is keyId-based, so a field inside the payload cannot add to "
    "it — a forged issuer alongside a valid signature proves the key, not the claim. (The ENTITLEMENT "
    "issuer is a different domain and IS bound, in the receipt verifier.)",
}


def _signed_metadata_fields() -> set[str]:
    """Every field the REAL Core-signed golden carries, top-level and per package entry."""
    golden = json.loads(Path("tests/fixtures/cross_repo_release_golden.json").read_text(encoding="utf-8"))
    metadata = json.loads(base64.b64decode(golden["releaseMetadataBytes"]).decode("utf-8"))
    fields = {key for key in metadata if key != "packages"}
    for package in metadata["packages"]:
        fields |= {f"packages[].{key}" for key in package}
    return fields


def test_every_signed_metadata_field_carries_a_binding_ruling() -> None:
    fields = _signed_metadata_fields()

    # Guard the guard. The golden was hand-built until this round and omitted byteSize entirely, so a
    # ruling table built against it described a document Core does not emit. If this enumerator ever
    # reads a stub again, the subset check below becomes a rubber stamp.
    assert fields >= {"schema", "coreVersion", "channel", "issuer", "packages[].sha256", "packages[].byteSize"}, (
        f"the signed-metadata enumerator found {sorted(fields)} — the golden is not a real Core "
        f"artifact, so this ratchet would pass vacuously. Regenerate it with "
        f"scripts/tools/emit-release-golden.mjs in the Core repo."
    )

    unruled = fields - set(METADATA_RULINGS)
    assert unruled == set(), (
        f"signed metadata fields with no binding ruling: {sorted(unruled)}. Core signs them, so either "
        f"bind them at install, or allowlist them with the reason they cannot influence anything."
    )


def _installer_entry_fields() -> set[str]:
    """The keys `install_from_authorization` copies out of the server response into the entry."""
    from verifysignal_spec.runtime import distribution

    source = Path(distribution.__file__).read_text(encoding="utf-8")
    start = source.index("def install_from_authorization")
    body = source[start : source.index("\ndef ", start + 1)]
    return {line.split('"')[1] for line in body.splitlines() if line.strip().startswith('"') and '":' in line}


def test_every_installer_entry_field_carries_a_binding_ruling() -> None:
    # The ratchet itself. A new field added to the entry without a ruling here fails this test rather
    # than silently becoming a trusted input from an untrusted source.
    fields = _installer_entry_fields()

    # Guard the guard: this reads the source, so a refactor could make it parse ZERO fields — and an
    # empty set trivially satisfies the subset check below, turning the ratchet into a rubber stamp.
    assert fields >= {"coreVersion", "sha256", "artifactName", "url", "signature"}, (
        f"the entry-field parser found {sorted(fields)} — it no longer sees install_from_authorization's "
        f"fields, so this ratchet would pass vacuously. Fix the parser, not this assertion."
    )

    unruled = fields - set(FIELD_RULINGS)
    assert unruled == set(), (
        f"installer entry fields with no binding ruling: {sorted(unruled)}. Every field comes from the "
        f"untrusted distribution server — bind it to the signed metadata, or allowlist it with a reason."
    )


def test_signed_metadata_binds_the_artifact_filename() -> None:
    # The trustworthy value already exists: real Core-signed metadata carries packages[].filename (see
    # tests/fixtures/cross_repo_release_golden.json) and the BE already cross-checks it at
    # registration. The Spec was the only consumer not binding it.
    entry = signed_manifest_entry(
        platform="darwin-arm64", sha256="a" * 64, artifactName="verifysignal-core-darwin-arm64.tar.gz"
    )
    assert verify_release_authenticity(entry) is None

    repointed = {**entry, "artifactName": "evil.tar.gz"}
    blocker = verify_release_authenticity(repointed)
    assert blocker is not None
    assert blocker.code == "artifact.authenticity-failed"


def test_signed_metadata_binds_its_own_schema() -> None:
    # A signature proves WHO signed, never WHAT KIND of document was signed. release_signature.py
    # checks a `schema` on the SIGNATURE RECORD — the unsigned wrapper, freely attacker-mutable — so
    # the signed payload's own schema must be checked here, or a foreign document signed by a trusted
    # key could be replayed as a release.
    entry = signed_manifest_entry(platform="darwin-arm64", sha256="a" * 64, signed_schema="attacker.release/v999")
    blocker = verify_release_authenticity(entry)
    assert blocker is not None
    assert blocker.code == "artifact.authenticity-failed"


def _signed_tarball(path: Path) -> str:
    with tarfile.open(path, "w:gz") as archive:
        data = json.dumps({"executable": "bin/verifysignal-core"}).encode()
        info = tarfile.TarInfo("verifysignal-core/manifest.json")
        info.size = len(data)
        archive.addfile(info, io.BytesIO(data))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_a_hostile_artifact_name_cannot_write_outside_the_scratch_dir(tmp_path: Path) -> None:
    # The original bug's reproduction, kept as the regression. An ABSOLUTE name is the realistic
    # shape: `Path(temp_dir) / "/abs/path"` discards temp_dir entirely, so the attacker needs no
    # knowledge of the scratch directory — unlike `..` traversal, which must guess its depth.
    #
    # Rejecting the install is NOT enough, which is the whole point: the write happened BEFORE
    # verification, so the bytes were already on disk by the time the verdict came in. The assertion
    # is that the file never appears at all, on the REJECTION path.
    victim = tmp_path / "victim.txt"
    payload = tmp_path / "payload.tar.gz"
    _signed_tarball(payload)

    entry = signed_manifest_entry(
        platform="darwin-arm64",
        sha256="b" * 64,  # forces verification to fail — bytes must not be on disk regardless
        artifactName=str(victim),
        url=payload.as_uri(),
    )

    runtime, blocker = install_from_manifest(entry)

    assert runtime is None
    assert blocker is not None
    assert not victim.exists(), (
        f"install wrote to an attacker-chosen path ({victim}) before verifying anything — rejecting "
        f"the release afterwards does not un-write the bytes."
    )


def test_a_benign_install_still_works(tmp_path: Path) -> None:
    # Scope guard: killing the write primitive must not kill the installer. A well-formed, genuinely
    # signed release still installs — otherwise the test above would pass trivially on a broken path.
    payload = tmp_path / "verifysignal-core-darwin-arm64.tar.gz"
    digest = _signed_tarball(payload)
    entry = signed_manifest_entry(
        platform="darwin-arm64",
        sha256=digest,
        artifactName=payload.name,
        url=payload.as_uri(),
    )

    assert verify_release_authenticity(entry) is None
