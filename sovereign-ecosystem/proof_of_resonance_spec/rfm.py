"""TP-102 Regenerative Finance Metrics (RFM) scoring from verified GTRs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from greentelemetry_protocol_spec.gtr import gtr_trust_score
from greentelemetry_protocol_spec.models import MeasurementType, SourceType

from .models import (
    PHASE1_ORACLE_PROFILE,
    RegenerativeFinanceMetrics,
    ScoringProfile,
)

if TYPE_CHECKING:
    from greentelemetry_protocol_spec.models import Tp101GreenTelemetryRecord

# RIV unit weights — normalized impact units per measurement type (Phase 1 table).
_RIV_WEIGHT: dict[MeasurementType, float] = {
    MeasurementType.CO2E: 1.0,
    MeasurementType.CH4: 0.85,
    MeasurementType.N2O: 0.85,
    MeasurementType.ENERGY_KWH: 0.05,
    MeasurementType.ENERGY_MJ: 0.04,
    MeasurementType.WATER_M3: 0.2,
    MeasurementType.BIODIVERSITY: 0.5,
    MeasurementType.OFFSET_CREDIT: 1.0,
    MeasurementType.CUSTOM: 0.1,
}

# Source-type multipliers for EQS diversity.
_SOURCE_EQS_FACTOR: dict[SourceType, float] = {
    SourceType.SENSOR: 1.0,
    SourceType.MANUAL: 0.75,
    SourceType.CERTIFIED_AUDITOR: 1.0,
    SourceType.API: 0.9,
}


def compute_eqs(
    tp101: Tp101GreenTelemetryRecord,
    *,
    binding_attestation_score: int | None = None,
) -> float:
    """Evidence Quality Score in [0, 1].

    Combines TP-101 attestation trust, source-type weighting, and optional
    Tegalid binding attestation (identity gate — not a substitute for EQS).
    """
    trust = gtr_trust_score(tp101)
    source_factor = _SOURCE_EQS_FACTOR.get(tp101.source_type, 0.85)
    eqs = trust * source_factor
    if binding_attestation_score is not None:
        identity_factor = min(1.0, binding_attestation_score / 100.0)
        eqs = round(min(1.0, eqs * 0.7 + identity_factor * 0.3), 4)
    return round(min(1.0, max(0.0, eqs)), 4)


def compute_riv(tp101: Tp101GreenTelemetryRecord) -> float:
    """Regenerative Impact Value — normalized non-negative decimal."""
    weight = _RIV_WEIGHT.get(tp101.measurement_type, 0.1)
    raw = abs(float(tp101.value)) * weight
    return round(max(0.0, raw), 6)


def compute_evidence_resonance(eqs: float, riv: float, consensus_confidence: float) -> int:
    """Map RFM tuple to a 0–100 evidence resonance centile."""
    riv_factor = min(1.0, riv / 1000.0) if riv > 0 else 0.0
    composite = (eqs * 0.5) + (riv_factor * 0.25) + (consensus_confidence * 0.25)
    return int(round(min(1.0, max(0.0, composite)) * 100))


def score_verified_gtr(
    tp101: Tp101GreenTelemetryRecord,
    *,
    gtr_hash: str,
    binding_attestation_score: int | None = None,
    consensus_confidence: float | None = None,
    scoring_profile: ScoringProfile = ScoringProfile.PHASE1_ORACLE,
) -> RegenerativeFinanceMetrics:
    """Score a verified TP-101 GTR (post-oracle)."""
    eqs = compute_eqs(tp101, binding_attestation_score=binding_attestation_score)
    riv = compute_riv(tp101)
    if consensus_confidence is None:
        consensus_confidence = 1.0 if scoring_profile == ScoringProfile.PHASE1_ORACLE else 0.0
    resonance = compute_evidence_resonance(eqs, riv, consensus_confidence)
    return RegenerativeFinanceMetrics(
        rfm_id=str(uuid.uuid4()),
        gtr_id=tp101.gtr_id,
        gtr_hash=gtr_hash,
        eqs=eqs,
        riv=riv,
        consensus_confidence=round(consensus_confidence, 4),
        resonance_score=resonance,
        scoring_profile=scoring_profile,
        scored_at=datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        measurement_type=tp101.measurement_type.value,
        source_id=tp101.source_id,
        binding_attestation_score=binding_attestation_score,
    )


def phase1_oracle_consensus() -> float:
    """Single-oracle Phase 1 profile assigns full consensus confidence."""
    return 1.0
