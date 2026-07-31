"""TP-101 GreenTelemetry Record (GTR) helpers.

See docs/standards/TP-101-GREENTELEMETRY.md.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum

from .models import SovereignNodeTelemetry, Tp101GreenTelemetryRecord, Tp101GreenTelemetryRecord

TP101_STANDARD_ID = "TP-101"
GTR_SCHEMA_VERSION = "1.0"
GTR_SCHEMA_VERSION = "1.0"


class ReportingMode(str, Enum):
    """How the producer delivered this GTR to the oracle."""

    STREAM = "stream"
    BATCH = "batch"


def compute_gtr_hash(tp101: Tp101GreenTelemetryRecord) -> str:
    """Stable SHA-256 over canonical TP-101 GTR JSON."""
    canonical = json.dumps(tp101.to_dict(), separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


def compute_legacy_hash(telemetry: SovereignNodeTelemetry) -> str:
    """Legacy hash over sovereign node envelope (pre-v1.3 producers)."""
    canonical = json.dumps(telemetry.to_dict(), separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(canonical.encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class GreenTelemetryRecord:
    """Verified TP-101 GTR at the oracle edge."""

    tp101: Tp101GreenTelemetryRecord
    record_hash: str
    legacy: SovereignNodeTelemetry
    protocol_standard: str = TP101_STANDARD_ID

    @classmethod
    def from_validated(
        cls,
        tp101: Tp101GreenTelemetryRecord,
        legacy: SovereignNodeTelemetry,
    ) -> GreenTelemetryRecord:
        return cls(
            tp101=tp101,
            legacy=legacy,
            record_hash=compute_gtr_hash(tp101),
        )


def gtr_trust_score(tp101: Tp101GreenTelemetryRecord) -> float:
    """Aggregate trust from attestation count and confidence scores (TP-101)."""
    if not tp101.attestations:
        return 0.0
    count_factor = min(1.0, 0.55 + (len(tp101.attestations) - 1) * 0.15)
    confidences = [
        att.confidence for att in tp101.attestations if att.confidence is not None
    ]
    confidence_factor = sum(confidences) / len(confidences) if confidences else 0.85
    return round(min(1.0, count_factor * confidence_factor), 2)
