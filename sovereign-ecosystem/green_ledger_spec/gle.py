"""Build GreenLedger Entry (GLE) records from submitted mint queue rows."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from .models import (
    AttestationSummaryItem,
    GreenLedgerEntry,
    MerkleProof,
    RetentionClass,
)


def _iso_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _attestation_summary(tp101: dict[str, Any]) -> tuple[AttestationSummaryItem, ...]:
    items: list[AttestationSummaryItem] = []
    for att in tp101.get("attestations") or []:
        items.append(
            AttestationSummaryItem(
                attester_id=str(att["attester_id"]),
                attester_type=str(att["attester_type"]),
                confidence=att.get("confidence"),
            )
        )
    if not items:
        raise ValueError("GTR must contain at least one attestation for GLE archival")
    return tuple(items)


def _merkle_proof_from_candidate(block_candidate: dict[str, Any]) -> MerkleProof | None:
    proof = block_candidate.get("merkle_proof")
    if not isinstance(proof, dict):
        batch = block_candidate.get("merkle_batch")
        if isinstance(batch, dict):
            content_hash = str(block_candidate.get("gtr_hash", ""))
            proofs = batch.get("proofs") or {}
            siblings = proofs.get(content_hash)
            root = batch.get("merkle_root")
            if root and siblings:
                return MerkleProof(merkle_root=str(root), siblings=tuple(str(s) for s in siblings))
        return None
    root = proof.get("merkle_root")
    siblings = proof.get("siblings")
    if root and siblings:
        return MerkleProof(
            merkle_root=str(root),
            siblings=tuple(str(s) for s in siblings),
        )
    return None


def build_greenledger_entry(
    *,
    block_candidate: dict[str, Any],
    ledger_ref: str,
    submitted_at: str | None = None,
    retention_class: RetentionClass = RetentionClass.STANDARD,
    tags: tuple[str, ...] = (),
    archive_timestamp: str | None = None,
) -> GreenLedgerEntry:
    """Materialize a GLE from a submitted TELEMETRY_MINT block candidate."""
    tp101 = block_candidate.get("tp101_record") or {}
    anchor = block_candidate.get("on_chain_anchor") or {}
    gtr_id = str(block_candidate.get("gtr_id") or tp101.get("gtr_id", ""))
    if not gtr_id:
        raise ValueError("gtr_id required for GreenLedger archival")

    content_hash = str(anchor.get("content_hash") or block_candidate.get("gtr_hash", ""))
    if len(content_hash) != 64:
        raise ValueError("content_hash must be 64-char SHA-256 hex")

    anchor_ts = anchor.get("anchor_timestamp")
    if not anchor_ts and submitted_at:
        anchor_ts = submitted_at
    if not anchor_ts:
        raise ValueError("anchor_timestamp required for GLE archival")

    measurement_ts = str(tp101.get("timestamp", ""))
    if not measurement_ts:
        raise ValueError("measurement_timestamp required from TP-101 GTR")

    summary = _attestation_summary(tp101)
    return GreenLedgerEntry(
        gle_id=str(uuid.uuid4()),
        gtr_id=gtr_id,
        ledger_ref=ledger_ref,
        content_hash=content_hash,
        source_id=str(tp101["source_id"]),
        measurement_type=str(tp101["measurement_type"]),
        value=float(tp101["value"]),
        unit=str(tp101["unit"]),
        measurement_timestamp=measurement_ts,
        anchor_timestamp=str(anchor_ts),
        archive_timestamp=archive_timestamp or _iso_now(),
        attestation_count=len(summary),
        attestation_summary=summary,
        retention_class=retention_class,
        merkle_proof=_merkle_proof_from_candidate(block_candidate),
        tags=tags,
    )
