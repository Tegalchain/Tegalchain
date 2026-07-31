"""Append TP-108 THIRD_PARTY attestations to archived GTR queue rows."""

from __future__ import annotations

import os
from typing import Any

from ai_attestation_spec.keys import resolve_ai_attester_secret
from ai_attestation_spec.validate import validate_tp108_metadata
from greentelemetry_protocol_spec.signing import (
    SignatureVerificationError,
    verify_gtr_ed25519_attestation,
)
from tegalchain.queue.store import MintQueueRecord, MintQueueStore

PRIMARY_ATTESTER_TYPES = frozenset({"DEVICE", "OPERATOR", "REGULATORY"})


class Tp108AppendError(Exception):
    """Attestation append rejected."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def tp108_validation_enabled() -> bool:
    return os.environ.get("MINT_WORKER_VALIDATE_TP108", "").lower() in {
        "1",
        "true",
        "yes",
    }


def _attestation_summary(tp101: dict[str, Any]) -> list[dict[str, Any]]:
    summary: list[dict[str, Any]] = []
    for att in tp101.get("attestations") or []:
        item: dict[str, Any] = {
            "attester_id": str(att["attester_id"]),
            "attester_type": str(att["attester_type"]),
        }
        if att.get("confidence") is not None:
            item["confidence"] = att["confidence"]
        summary.append(item)
    return summary


def validate_ai_attestation(tp101: dict[str, Any], attestation: dict[str, Any]) -> None:
    if attestation.get("attester_type") != "THIRD_PARTY":
        raise Tp108AppendError("append attestation must be THIRD_PARTY", 422)

    attester_id = str(attestation.get("attester_id", ""))
    secret = resolve_ai_attester_secret(attester_id)
    if secret is None:
        raise Tp108AppendError(f"unknown AI attester_id: {attester_id!r}", 403)

    existing = tp101.get("attestations") or []
    if not any(att.get("attester_type") in PRIMARY_ATTESTER_TYPES for att in existing):
        raise Tp108AppendError(
            "GTR must retain a DEVICE/OPERATOR/REGULATORY attestation before AI append",
            422,
        )

    metadata = attestation.get("metadata") or {}
    tp108 = metadata.get("tp108")
    if not isinstance(tp108, dict):
        raise Tp108AppendError("THIRD_PARTY attestation requires metadata.tp108", 422)

    if tp108_validation_enabled():
        validate_tp108_metadata(tp108)

    unsigned = {key: value for key, value in tp101.items() if key != "attestations"}
    try:
        verify_gtr_ed25519_attestation(unsigned, attestation, secret)
    except SignatureVerificationError as exc:
        raise Tp108AppendError(str(exc), 401) from exc


def append_attestation(
    store: MintQueueStore,
    gtr_id: str,
    attestation: dict[str, Any],
) -> MintQueueRecord:
    """Validate and persist a THIRD_PARTY attestation on an existing GTR."""
    record = store.fetch_by_gtr_id(gtr_id)
    if record is None:
        raise Tp108AppendError("gtr_id not found", 404)

    block_candidate = dict(record.block_candidate)
    tp101 = dict(block_candidate.get("tp101_record") or {})
    if not tp101:
        raise Tp108AppendError("stored record has no tp101_record", 422)

    validate_ai_attestation(tp101, attestation)

    attestations = list(tp101.get("attestations") or [])
    attester_id = str(attestation["attester_id"])
    tp108 = (attestation.get("metadata") or {}).get("tp108") or {}
    claim_type = tp108.get("claim_type")
    for existing in attestations:
        if existing.get("attester_id") != attester_id:
            continue
        existing_claim = ((existing.get("metadata") or {}).get("tp108") or {}).get("claim_type")
        if existing_claim == claim_type:
            raise Tp108AppendError(
                f"duplicate TP-108 claim {claim_type!r} from {attester_id!r}",
                409,
            )

    attestations.append(attestation)
    tp101["attestations"] = attestations
    block_candidate["tp101_record"] = tp101
    updated = store.update_block_candidate(record.id, block_candidate)

    gle = store.fetch_greenledger_by_gtr_id(gtr_id)
    if gle is not None:
        gle["attestation_count"] = len(attestations)
        gle["attestation_summary"] = _attestation_summary(tp101)
        store.save_greenledger_entry(gle)

    return updated
