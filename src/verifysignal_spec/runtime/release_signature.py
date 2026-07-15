from __future__ import annotations

import base64
import json
import os

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
from cryptography.hazmat.primitives.serialization import load_der_public_key, load_pem_public_key

# Runtime-release signing keys are a SEPARATE trust domain from entitlement-receipt keys.
# Core signs a detached Ed25519 signature over the EXACT release-metadata file bytes. This
# module verifies that signature against a trusted release key so an install can prove the
# downloaded archive bytes were signed by an accepted release key.
#
# Trust anchors: production keys from VERIFYSIGNAL_RUNTIME_RELEASE_PUBLIC_KEYS (JSON:
# keyId -> PEM or base64-DER SPKI), plus the shipped TEST key ONLY when
# VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS == "1". With neither configured the trust set is empty
# and every verification fails closed.

TEST_RELEASE_KEY_ID = "verifysignal-core-release-test-key"
TEST_RELEASE_PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEA9cu+k/slRJsVRXV7mGPjJYtsqNO6DFFUi8phMq3Hiqw=
-----END PUBLIC KEY-----
"""


def _load_public_key(raw: str) -> Ed25519PublicKey:
    text = raw.replace("\\n", "\n").strip()
    if "PUBLIC KEY" in text:
        key = load_pem_public_key(text.encode("utf-8"))
    else:
        key = load_der_public_key(base64.b64decode(text))
    if not isinstance(key, Ed25519PublicKey):
        raise ValueError("Release signing key is not an Ed25519 public key.")
    return key


def trusted_release_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    configured = os.environ.get("VERIFYSIGNAL_RUNTIME_RELEASE_PUBLIC_KEYS")
    if configured:
        try:
            parsed = json.loads(configured)
        except (ValueError, TypeError):
            parsed = {}
        if isinstance(parsed, dict):
            for key_id, pem in parsed.items():
                if isinstance(key_id, str) and isinstance(pem, str) and pem:
                    keys[key_id] = pem
    if os.environ.get("VERIFYSIGNAL_ALLOW_TEST_RELEASE_KEYS") == "1":
        keys[TEST_RELEASE_KEY_ID] = TEST_RELEASE_PUBLIC_KEY_PEM
    return keys


def verify_release_signature(
    metadata_bytes: bytes,
    signature: dict[str, object],
    trusted: dict[str, str] | None = None,
) -> tuple[bool, str | None]:
    """Verify a detached Ed25519 release signature over the exact metadata bytes.

    Returns ``(ok, keyId)``. ``ok`` is True only when the signature verifies against a
    trusted release key.
    """
    trusted = trusted_release_keys() if trusted is None else trusted
    if signature.get("schema") != "verifysignal.runtime-signature/v1" or signature.get("algorithm") != "ed25519":
        return False, None
    key_id = signature.get("keyId")
    value = signature.get("signature")
    if not isinstance(key_id, str) or not key_id or not isinstance(value, str) or not value:
        return False, None
    pem = trusted.get(key_id)
    if not pem:
        return False, None
    try:
        public_key = _load_public_key(pem)
        public_key.verify(base64.b64decode(value), metadata_bytes)
    except (InvalidSignature, ValueError, TypeError):
        return False, None
    return True, key_id
