"""TP-102 validator Resonance Score (R) — dimension calculators."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# Composite weights (must sum to 1.0).
WEIGHT_R_ENV = 0.30
WEIGHT_R_GOV = 0.25
WEIGHT_R_UP = 0.25
WEIGHT_R_CMP = 0.20

# R_env sub-factor weights when monthly GTRs are present.
_ENV_CARBON_WEIGHT = 0.40
_ENV_RENEWABLE_WEIGHT = 0.35
_ENV_OFFSET_WEIGHT = 0.25

# Governance abstention penalty (applied to R_gov before clamping).
GOVERNANCE_ABSTENTION_PENALTY = 0.10
GOVERNANCE_ABSTENTION_THRESHOLD = 0.40

# Compliance penalties and epoch decay.
COMPLIANCE_DECAY_PER_EPOCH = 0.02


class ComplianceOffence(str, Enum):
    DOUBLE_SIGNING = "DOUBLE_SIGNING"
    EQUIVOCATION_FINALITY = "EQUIVOCATION_FINALITY"
    INVALID_BLOCK = "INVALID_BLOCK"
    GTR_TIMESTAMP_VIOLATION = "GTR_TIMESTAMP_VIOLATION"
    API_RATE_LIMIT_ABUSE = "API_RATE_LIMIT_ABUSE"


COMPLIANCE_PENALTIES: dict[ComplianceOffence, float] = {
    ComplianceOffence.DOUBLE_SIGNING: 0.40,
    ComplianceOffence.EQUIVOCATION_FINALITY: 0.20,
    ComplianceOffence.INVALID_BLOCK: 0.15,
    ComplianceOffence.GTR_TIMESTAMP_VIOLATION: 0.10,
    ComplianceOffence.API_RATE_LIMIT_ABUSE: 0.05,
}


@dataclass(frozen=True, slots=True)
class EnvironmentalInputs:
    """TP-101 GreenTelemetry inputs for R_env."""

    gtr_count_current_month: int
    carbon_intensity_kwh_per_block: float
    network_median_carbon_intensity: float
    renewable_ratio: float
    offset_coverage: float


@dataclass(frozen=True, slots=True)
class GovernanceInputs:
    vote_participation_rate: float
    policy_consistency_rate: float
    proposal_acceptance_rate: float
    abstention_rate: float


@dataclass(frozen=True, slots=True)
class UptimeInputs:
    blocks_produced: int
    blocks_assigned: int
    propagation_time_ms: float
    network_median_propagation_ms: float
    network_p95_propagation_ms: float


@dataclass(frozen=True, slots=True)
class ComplianceInputs:
    offences: tuple[ComplianceOffence, ...]
    epochs_since_last_offence: int


def _clamp_unit(value: float) -> float:
    return round(min(1.0, max(0.0, value)), 4)


def compute_r_env(inputs: EnvironmentalInputs) -> float:
    """Environmental dimension R_env from validator GreenTelemetry (TP-101).

    Validators with zero GTR submissions in the current calendar month MUST
    receive R_env = 0.0.
    """
    if inputs.gtr_count_current_month <= 0:
        return 0.0

    median = max(inputs.network_median_carbon_intensity, 1e-9)
    carbon_factor = 1.0 - min(1.0, inputs.carbon_intensity_kwh_per_block / median)
    renewable_factor = _clamp_unit(inputs.renewable_ratio)
    offset_factor = _clamp_unit(inputs.offset_coverage)
    score = (
        _ENV_CARBON_WEIGHT * carbon_factor
        + _ENV_RENEWABLE_WEIGHT * renewable_factor
        + _ENV_OFFSET_WEIGHT * offset_factor
    )
    return _clamp_unit(score)


def compute_r_gov(inputs: GovernanceInputs) -> float:
    """Governance dimension R_gov from TP-106 participation signals."""
    participation = _clamp_unit(inputs.vote_participation_rate)
    consistency = _clamp_unit(inputs.policy_consistency_rate)
    acceptance = _clamp_unit(inputs.proposal_acceptance_rate)
    score = participation * 0.50 + consistency * 0.30 + acceptance * 0.20
    if inputs.abstention_rate > GOVERNANCE_ABSTENTION_THRESHOLD:
        score -= GOVERNANCE_ABSTENTION_PENALTY
    return _clamp_unit(score)


def compute_latency_factor(
    propagation_time_ms: float,
    *,
    network_median_ms: float,
    network_p95_ms: float,
) -> float:
    """1.0 at median propagation; linear decay to 0.5 at the 95th percentile."""
    if network_p95_ms <= network_median_ms:
        return 1.0
    if propagation_time_ms <= network_median_ms:
        return 1.0
    if propagation_time_ms >= network_p95_ms:
        return 0.5
    span = network_p95_ms - network_median_ms
    excess = propagation_time_ms - network_median_ms
    return round(1.0 - (excess / span) * 0.5, 4)


def compute_r_up(inputs: UptimeInputs) -> float:
    """Uptime dimension R_up from block production reliability."""
    if inputs.blocks_assigned <= 0:
        return 0.0
    production_ratio = inputs.blocks_produced / inputs.blocks_assigned
    latency_factor = compute_latency_factor(
        inputs.propagation_time_ms,
        network_median_ms=inputs.network_median_propagation_ms,
        network_p95_ms=inputs.network_p95_propagation_ms,
    )
    return _clamp_unit(production_ratio * latency_factor)


def compute_r_cmp(inputs: ComplianceInputs) -> float:
    """Compliance dimension R_cmp — starts at 1.0, penalized by offences, decays over time."""
    score = 1.0
    for offence in inputs.offences:
        score -= COMPLIANCE_PENALTIES[offence]
    if inputs.epochs_since_last_offence > 0 and not inputs.offences:
        score += COMPLIANCE_DECAY_PER_EPOCH * inputs.epochs_since_last_offence
    return _clamp_unit(score)


def compute_resonance_score(
    r_env: float,
    r_gov: float,
    r_up: float,
    r_cmp: float,
) -> float:
    """Composite validator Resonance R in [0.0, 1.0]."""
    score = (
        WEIGHT_R_ENV * r_env
        + WEIGHT_R_GOV * r_gov
        + WEIGHT_R_UP * r_up
        + WEIGHT_R_CMP * r_cmp
    )
    return _clamp_unit(score)
