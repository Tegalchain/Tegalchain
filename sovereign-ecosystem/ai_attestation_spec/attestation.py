"""Build signed TP-108 THIRD_PARTY attestations for GTR append."""

from __future__ import annotations

from typing import Any

from greentelemetry_protocol_spec.signing import sign_gtr_ed25519
from greentelemetry_protocol_spec.tp101_builder import iso8601_now

from ai_attestation_spec.keys import DEFAULT_AI_ATTESTER_ID, resolve_ai_attester_secret


def unsigned_tp101_for_attestation(tp101: dict[str, Any]) -> dict[str, Any]:
    """GTR body used for attestation hashing (attestations excluded)."""
    return {key: value for key, value in tp101.items() if key != "attestations"}


def build_third_party_attestation(
    tp101: dict[str, Any],
    *,
    tp108: dict[str, Any],
    attester_id: str = DEFAULT_AI_ATTESTER_ID,
    signing_secret: bytes | None = None,
    confidence: float | None = None,
    attestation_timestamp: str | None = None,
) -> dict[str, Any]:
    """Return a signed THIRD_PARTY attestation dict ready for mint worker append."""
    secret = signing_secret if signing_secret is not None else resolve_ai_attester_secret(attester_id)
    if secret is None:
        raise ValueError(f"unknown AI attester_id: {attester_id!r}")

    unsigned = unsigned_tp101_for_attestation(tp101)
    signature = sign_gtr_ed25519(unsigned, secret)
    body: dict[str, Any] = {
        "attester_id": attester_id[:64],
        "attester_type": "THIRD_PARTY",
        "signature": signature,
        "timestamp": attestation_timestamp or iso8601_now(),
        "metadata": {"tp108": tp108},
    }
    if confidence is not None:
        body["confidence"] = confidence
    return body


def tp108_metadata_from_corroboration(
    result: Any,
    *,
    model_profile: str,
    model_version: str = "deterministic-v1",
) -> dict[str, Any]:
    """Map CorroborationResult → metadata.tp108 object."""
    return {
        "protocol_standard": "TP-108",
        "schema_version": "1.0.0",
        "claim_type": "CORROBORATION",
        "model_profile": model_profile,
        "inputs_hash": result.inputs_hash,
        "verdict": result.verdict.value,
        "score": round(result.score, 2),
        "subject_gtr_id": result.public_inputs.get("gtr_id"),
        "corroboration_refs": [result.public_inputs.get("cdr_sha256", "")],
        "model_version": model_version,
    }
