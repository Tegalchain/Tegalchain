"""TP-103 GreenLedger data models and constants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

TP103_STANDARD_ID = "TP-103"
GLE_SCHEMA_VERSION = "1.0"

# Minimum retention windows (years) by class.
RETENTION_YEARS = {
    "STANDARD": 7,
    "REGULATORY": 10,
    "PERMANENT": None,
}


class RetentionClass(str, Enum):
    STANDARD = "STANDARD"
    REGULATORY = "REGULATORY"
    PERMANENT = "PERMANENT"


@dataclass(frozen=True, slots=True)
class AttestationSummaryItem:
    attester_id: str
    attester_type: str
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "attester_id": self.attester_id,
            "attester_type": self.attester_type,
        }
        if self.confidence is not None:
            body["confidence"] = self.confidence
        return body


@dataclass(frozen=True, slots=True)
class MerkleProof:
    merkle_root: str
    siblings: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "merkle_root": self.merkle_root,
            "siblings": list(self.siblings),
        }


@dataclass(frozen=True, slots=True)
class GreenLedgerEntry:
    """GreenLedger Entry (GLE) — archival representation of a finalized GTR."""

    gle_id: str
    gtr_id: str
    ledger_ref: str
    content_hash: str
    source_id: str
    measurement_type: str
    value: float
    unit: str
    measurement_timestamp: str
    anchor_timestamp: str
    archive_timestamp: str
    attestation_count: int
    attestation_summary: tuple[AttestationSummaryItem, ...]
    retention_class: RetentionClass
    merkle_proof: MerkleProof | None = None
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "gle_id": self.gle_id,
            "gtr_id": self.gtr_id,
            "ledger_ref": self.ledger_ref,
            "content_hash": self.content_hash,
            "source_id": self.source_id,
            "measurement_type": self.measurement_type,
            "value": self.value,
            "unit": self.unit,
            "measurement_timestamp": self.measurement_timestamp,
            "anchor_timestamp": self.anchor_timestamp,
            "archive_timestamp": self.archive_timestamp,
            "attestation_count": self.attestation_count,
            "attestation_summary": [item.to_dict() for item in self.attestation_summary],
            "retention_class": self.retention_class.value,
            "schema_version": GLE_SCHEMA_VERSION,
            "protocol_standard": TP103_STANDARD_ID,
        }
        if self.merkle_proof is not None:
            body["merkle_proof"] = self.merkle_proof.to_dict()
        if self.tags:
            body["tags"] = list(self.tags)
        return body
