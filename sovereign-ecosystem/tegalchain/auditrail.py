"""TP-103 Auditrail correlation — link gtr_id to on-chain submit_ref post-commit."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from tegalchain.queue.store import MintQueueRecord, MintQueueStore


@dataclass(frozen=True, slots=True)
class AuditrailCorrelation:
    gtr_id: str
    queue_id: int
    telemetry_hash: str
    submit_ref: str
    submitted_at: str
    content_hash: str
    auditrail_record_type: str
    anchor_timestamp: str | None
    tegalid_did: str | None
    project_id: str | None
    binding_id: str | None
    correlated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "gtr_id": self.gtr_id,
            "queue_id": self.queue_id,
            "telemetry_hash": self.telemetry_hash,
            "submit_ref": self.submit_ref,
            "submitted_at": self.submitted_at,
            "content_hash": self.content_hash,
            "auditrail_record_type": self.auditrail_record_type,
            "anchor_timestamp": self.anchor_timestamp,
            "tegalid_did": self.tegalid_did,
            "project_id": self.project_id,
            "binding_id": self.binding_id,
            "correlated_at": self.correlated_at,
        }


def _iso_now() -> str:
    return datetime.now(tz=UTC).isoformat()


def build_auditrail_correlation(
    record: MintQueueRecord,
    *,
    block_candidate: dict[str, Any],
) -> AuditrailCorrelation:
    if not record.submit_ref or not record.submitted_at:
        raise ValueError("submitted queue record required for Auditrail correlation")
    gtr_id = record.gtr_id or str(block_candidate.get("gtr_id", ""))
    if not gtr_id:
        raise ValueError("gtr_id missing from queue record")

    anchor = block_candidate.get("on_chain_anchor") or {}
    content_hash = str(anchor.get("content_hash", record.telemetry_hash))
    tp101 = block_candidate.get("tp101_record") or {}

    return AuditrailCorrelation(
        gtr_id=gtr_id,
        queue_id=record.id,
        telemetry_hash=record.telemetry_hash,
        submit_ref=str(record.submit_ref),
        submitted_at=str(record.submitted_at),
        content_hash=content_hash,
        auditrail_record_type=str(
            block_candidate.get("auditrail_record_type", "GREETELEMETRY")
        ),
        anchor_timestamp=anchor.get("anchor_timestamp"),
        tegalid_did=block_candidate.get("tegalid_did") or record.identity.get("node_id"),
        project_id=tp101.get("project_id") or block_candidate.get("project_id"),
        binding_id=tp101.get("binding_id") or block_candidate.get("binding_id"),
        correlated_at=_iso_now(),
    )


def correlate_submitted_record(
    store: MintQueueStore,
    record: MintQueueRecord,
    *,
    block_candidate: dict[str, Any],
) -> AuditrailCorrelation:
    """Persist Auditrail correlation and GreenLedger GLE after chain submit."""
    from tegalchain.greenledger import archive_submitted_gtr

    correlation = build_auditrail_correlation(record, block_candidate=block_candidate)
    store.save_auditrail_correlation(correlation.to_dict())
    if block_candidate.get("tp101_record"):
        archive_submitted_gtr(store, record, block_candidate=block_candidate)
    return correlation
