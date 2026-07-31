"""TP-103 on-chain GTR anchor payload (hash + summary only; full GTR off-chain)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from greentelemetry_protocol_spec.gtr import compute_gtr_hash
from greentelemetry_protocol_spec.models import Tp101GreenTelemetryRecord

from .block import merkle_proof


@dataclass(frozen=True, slots=True)
class GtrOnChainAnchor:
    gtr_id: str
    content_hash: str
    attester_ids: tuple[str, ...]
    measurement_type: str
    timestamp: str
    anchor_timestamp: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "GTR_ANCHOR",
            "gtr_id": self.gtr_id,
            "content_hash": self.content_hash,
            "attester_ids": list(self.attester_ids),
            "measurement_type": self.measurement_type,
            "timestamp": self.timestamp,
        }
        if self.anchor_timestamp is not None:
            payload["anchor_timestamp"] = self.anchor_timestamp
        return payload


@dataclass(frozen=True, slots=True)
class MerkleAnchorBatch:
    """Merkle root anchor for high-throughput ingestion (>100 records/s target)."""

    merkle_root: str
    anchor_timestamp: str
    record_count: int
    content_hashes: tuple[str, ...]
    proofs: dict[str, list[str]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": "GTR_MERKLE_BATCH",
            "merkle_root": self.merkle_root,
            "anchor_timestamp": self.anchor_timestamp,
            "record_count": self.record_count,
            "content_hashes": list(self.content_hashes),
            "proofs": self.proofs,
        }


def iso_anchor_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_on_chain_anchor(
    record: Tp101GreenTelemetryRecord,
    *,
    anchor_timestamp: str | None = None,
) -> GtrOnChainAnchor:
    """Build TP-101 on-chain summary; full GTR remains in TP-103 GreenLedger store."""
    return GtrOnChainAnchor(
        gtr_id=record.gtr_id,
        content_hash=compute_gtr_hash(record),
        attester_ids=tuple(att.attester_id for att in record.attestations),
        measurement_type=record.measurement_type.value,
        timestamp=record.timestamp,
        anchor_timestamp=anchor_timestamp,
    )


def finalize_anchor_for_submit(anchor: GtrOnChainAnchor) -> GtrOnChainAnchor:
    if anchor.anchor_timestamp is not None:
        return anchor
    return GtrOnChainAnchor(
        gtr_id=anchor.gtr_id,
        content_hash=anchor.content_hash,
        attester_ids=anchor.attester_ids,
        measurement_type=anchor.measurement_type,
        timestamp=anchor.timestamp,
        anchor_timestamp=iso_anchor_now(),
    )


def build_merkle_batch_anchors(
    anchors: list[GtrOnChainAnchor],
    *,
    anchor_timestamp: str | None = None,
) -> MerkleAnchorBatch:
    """Batch multiple GTR content hashes under one on-chain Merkle root."""
    if not anchors:
        raise ValueError("anchors must not be empty")
    leaves = [anchor.content_hash for anchor in anchors]
    proofs: dict[str, list[str]] = {}
    for index, anchor in enumerate(anchors):
        proofs[anchor.gtr_id] = merkle_proof(index, leaves)
    from .block import merkle_root_from_hashes

    root = merkle_root_from_hashes(leaves)
    return MerkleAnchorBatch(
        merkle_root=root,
        anchor_timestamp=anchor_timestamp or iso_anchor_now(),
        record_count=len(anchors),
        content_hashes=tuple(leaves),
        proofs=proofs,
    )


def merkle_batch_recommended(records_per_second: float, *, threshold: float = 100.0) -> bool:
    return records_per_second > threshold
