"""TP-102 data models and constants."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

TP102_STANDARD_ID = "TP-102"
RFM_SCHEMA_VERSION = "1.0"

# Phase 1 oracle stub — single endorser implies full consensus confidence.
PHASE1_ORACLE_PROFILE = "phase1_oracle"
POREF_FULL_PROFILE = "poref_full"

# Default PoREF eligibility thresholds (R in [0.0, 1.0]).
DEFAULT_MIN_RESONANCE_BLOCK_PRODUCTION = 0.40
DEFAULT_MIN_R_ENV_BLOCK_PRODUCTION = 0.20
DEFAULT_MIN_RESONANCE_GOVERNANCE = 0.40

# Validator bond and registration (TP-106 / Identity Registry).
MIN_STAKE_TEGAL = 10_000
MIN_BOND_AFTER_GRACE = 8_000
BOND_GRACE_DAYS = 7
MIN_IDENTITY_TIER = 2
BASELINE_GTR_DAYS = 90
SUSPENSION_EPOCHS_BELOW_MIN_R = 3


class ScoringProfile(str, Enum):
    PHASE1_ORACLE = PHASE1_ORACLE_PROFILE
    POREF_FULL = POREF_FULL_PROFILE


class ValidatorClass(str, Enum):
    ENERGY = "ENERGY"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    COMMUNITY = "COMMUNITY"


class VoteDecision(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class RegenerativeFinanceMetrics:
    """PoRE output (RFM) for one verified GTR."""

    rfm_id: str
    gtr_id: str
    gtr_hash: str
    eqs: float
    riv: float
    consensus_confidence: float
    resonance_score: int
    scoring_profile: ScoringProfile
    scored_at: str
    measurement_type: str | None = None
    source_id: str | None = None
    binding_attestation_score: int | None = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "rfm_id": self.rfm_id,
            "gtr_id": self.gtr_id,
            "gtr_hash": self.gtr_hash,
            "schema_version": RFM_SCHEMA_VERSION,
            "protocol_standard": TP102_STANDARD_ID,
            "eqs": self.eqs,
            "riv": self.riv,
            "consensus_confidence": self.consensus_confidence,
            "resonance_score": self.resonance_score,
            "scoring_profile": self.scoring_profile.value,
            "scored_at": self.scored_at,
        }
        if self.measurement_type is not None:
            body["measurement_type"] = self.measurement_type
        if self.source_id is not None:
            body["source_id"] = self.source_id
        if self.binding_attestation_score is not None:
            body["binding_attestation_score"] = self.binding_attestation_score
        return body


@dataclass(frozen=True, slots=True)
class ValidatorResonanceDimensions:
    r_env: float
    r_gov: float
    r_up: float
    r_cmp: float

    def to_dict(self) -> dict[str, float]:
        return {
            "r_env": self.r_env,
            "r_gov": self.r_gov,
            "r_up": self.r_up,
            "r_cmp": self.r_cmp,
        }


@dataclass(frozen=True, slots=True)
class ValidatorResonanceProfile:
    validator_id: str
    validator_class: ValidatorClass
    resonance_score: float
    dimensions: ValidatorResonanceDimensions
    eligible_for_block_production: bool
    eligible_for_governance: bool
    scored_at: str
    scoring_profile: ScoringProfile
    gtr_count_current_month: int | None = None

    def to_dict(self) -> dict[str, Any]:
        body: dict[str, Any] = {
            "validator_id": self.validator_id,
            "validator_class": self.validator_class.value,
            "schema_version": RFM_SCHEMA_VERSION,
            "protocol_standard": TP102_STANDARD_ID,
            "resonance_score": self.resonance_score,
            "dimensions": self.dimensions.to_dict(),
            "eligible_for_block_production": self.eligible_for_block_production,
            "eligible_for_governance": self.eligible_for_governance,
            "scored_at": self.scored_at,
            "scoring_profile": self.scoring_profile.value,
        }
        if self.gtr_count_current_month is not None:
            body["gtr_count_current_month"] = self.gtr_count_current_month
        return body
