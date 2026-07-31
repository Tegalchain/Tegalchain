"""Ed25519 attestation and legacy HMAC signing for gretelemetry."""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any, Final

DEFAULT_HMAC_SECRET: Final[bytes] = b"sovereign-ecosystem-dev-key"

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
        Ed25519PublicKey,
    )
    from cryptography.exceptions import InvalidSignature
except ImportError:  # pragma: no cover
    Ed25519PrivateKey = None  # type: ignore[misc, assignment]
    Ed25519PublicKey = None  # type: ignore[misc, assignment]
    InvalidSignature = Exception  # type: ignore[misc, assignment]


class SignatureVerificationError(ValueError):
    """Raised when telemetry or GTR attestation verification fails."""


def unsigned_canonical_json(payload: dict[str, Any]) -> str:
    """Canonical JSON for signing legacy envelopes (all fields except signature)."""
    unsigned = {key: value for key, value in payload.items() if key != "signature"}
    return json.dumps(unsigned, separators=(",", ":"), sort_keys=True)


def unsigned_gtr_canonical_json(payload: dict[str, Any]) -> str:
    """Canonical JSON for TP-101 GTR hashing (all fields except attestations)."""
    unsigned = {key: value for key, value in payload.items() if key != "attestations"}
    return json.dumps(unsigned, separators=(",", ":"), sort_keys=True)


def gtr_canonical_hash(payload: dict[str, Any]) -> bytes:
    """SHA-256 digest over canonical GTR JSON (pre-attestation)."""
    return hashlib.sha256(unsigned_gtr_canonical_json(payload).encode()).digest()


def ed25519_private_key_from_secret(secret: bytes = DEFAULT_HMAC_SECRET) -> Ed25519PrivateKey:
    if Ed25519PrivateKey is None:
        raise RuntimeError(
            "cryptography is required for TP-101 Ed25519 attestations; "
            "pip install cryptography"
        )
    seed = hashlib.sha256(secret).digest()
    return Ed25519PrivateKey.from_private_bytes(seed)


def ed25519_public_key_from_secret(secret: bytes = DEFAULT_HMAC_SECRET) -> Ed25519PublicKey:
    return ed25519_private_key_from_secret(secret).public_key()


def signature_bytes_to_hex(signature: bytes) -> str:
    if len(signature) != 64:
        raise ValueError("Ed25519 signature must be 64 bytes")
    return signature.hex()


def signature_hex_to_bytes(signature: str) -> bytes:
    raw = signature.lower()
    if raw.startswith("0x"):
        raw = raw[2:]
    if len(raw) != 128 or not all(ch in "0123456789abcdef" for ch in raw):
        raise SignatureVerificationError("GTR attestation signature must be 64-byte hex")
    return bytes.fromhex(raw)


def sign_gtr_ed25519(
    payload: dict[str, Any],
    secret: bytes = DEFAULT_HMAC_SECRET,
) -> str:
    """Return 64-byte Ed25519 signature (hex) over the GTR canonical hash."""
    private_key = ed25519_private_key_from_secret(secret)
    digest = gtr_canonical_hash(payload)
    return signature_bytes_to_hex(private_key.sign(digest))


def verify_gtr_ed25519_attestation(
    payload: dict[str, Any],
    attestation: dict[str, Any],
    secret: bytes = DEFAULT_HMAC_SECRET,
) -> None:
    """Verify one Ed25519 attestation over the GTR canonical hash."""
    try:
        public_key = ed25519_public_key_from_secret(secret)
        signature = signature_hex_to_bytes(str(attestation["signature"]))
        public_key.verify(signature, gtr_canonical_hash(payload))
    except (InvalidSignature, ValueError, KeyError, TypeError) as exc:
        raise SignatureVerificationError("GTR Ed25519 attestation verification failed") from exc


def sign_payload(canonical_json: str, secret: bytes = DEFAULT_HMAC_SECRET) -> str:
    """Produce a deterministic HMAC-SHA256 signature over canonical telemetry JSON."""
    digest = hmac.new(secret, canonical_json.encode(), hashlib.sha256).hexdigest()
    return f"hmac-sha256:{digest}"


def verify_telemetry_signature(
    payload: dict[str, Any],
    secret: bytes = DEFAULT_HMAC_SECRET,
) -> None:
    """Verify HMAC on legacy telemetry payload."""
    signature = payload.get("signature")
    if not signature:
        raise SignatureVerificationError("Missing signature field")

    expected = sign_payload(unsigned_canonical_json(payload), secret)
    if not hmac.compare_digest(expected, signature):
        raise SignatureVerificationError("Telemetry signature verification failed")


def verify_gtr_attestations(
    payload: dict[str, Any],
    secret: bytes = DEFAULT_HMAC_SECRET,
) -> None:
    """Verify TP-101 GTR attestations (Ed25519 over canonical hash).

    Lab / Phase 1: DEVICE attestations use ``secret`` derived from the producer
    or tegalid binding HMAC secret when ``attester_id`` matches ``source_id``.
    """
    if Ed25519PrivateKey is None:
        raise RuntimeError(
            "cryptography is required for TP-101 Ed25519 attestations; "
            "pip install cryptography"
        )

    attestations = payload.get("attestations") or []
    if not attestations:
        raise SignatureVerificationError("GTR requires at least one attestation")

    source_id = str(payload.get("source_id", ""))
    verified = False
    for attestation in attestations:
        attester_id = str(attestation.get("attester_id", ""))
        attester_secret = secret if attester_id == source_id else secret
        try:
            verify_gtr_ed25519_attestation(payload, attestation, attester_secret)
            verified = True
            break
        except SignatureVerificationError:
            continue

    if not verified:
        raise SignatureVerificationError("GTR attestation verification failed")
