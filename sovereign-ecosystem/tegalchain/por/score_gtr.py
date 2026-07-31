"""TP-102 bridge hooks — score verified GTRs for PoRE consumer routing."""

from __future__ import annotations

from proof_of_resonance_spec.models import RegenerativeFinanceMetrics, ScoringProfile
from proof_of_resonance_spec.rfm import phase1_oracle_consensus, score_verified_gtr

from greentelemetry_protocol_spec.models import Tp101GreenTelemetryRecord


def score_gtr_for_por(
    tp101: Tp101GreenTelemetryRecord,
    *,
    gtr_hash: str,
    binding_attestation_score: int | None = None,
    scoring_profile: ScoringProfile = ScoringProfile.PHASE1_ORACLE,
) -> RegenerativeFinanceMetrics:
    """Compute RFM for a ledger-bound GTR at the bridge edge."""
    consensus = phase1_oracle_consensus()
    if scoring_profile != ScoringProfile.PHASE1_ORACLE:
        consensus = 0.0
    return score_verified_gtr(
        tp101,
        gtr_hash=gtr_hash,
        binding_attestation_score=binding_attestation_score,
        consensus_confidence=consensus,
        scoring_profile=scoring_profile,
    )
