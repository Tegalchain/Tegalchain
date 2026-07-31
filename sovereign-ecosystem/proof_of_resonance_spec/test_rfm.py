"""Tests for TP-102 RFM scoring."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from proof_of_resonance_spec.eligibility import score_validator  # noqa: E402
from proof_of_resonance_spec.models import ScoringProfile, ValidatorClass, ValidatorResonanceDimensions  # noqa: E402
from proof_of_resonance_spec.rfm import compute_eqs, compute_riv, score_verified_gtr  # noqa: E402
from proof_of_resonance_spec.validate import validate_por_payload  # noqa: E402


class RfmScoringTests(unittest.TestCase):
    def test_eqs_from_signed_gtr(self) -> None:
        record = build_signed_tp101_gtr(
            source_id="por-node-1",
            source_type=SourceType.SENSOR,
            measurement_type=MeasurementType.ENERGY_KWH,
            value=42.0,
            unit="kWh",
        )
        eqs = compute_eqs(record)
        self.assertGreaterEqual(eqs, 0.0)
        self.assertLessEqual(eqs, 1.0)

    def test_binding_score_boosts_eqs(self) -> None:
        record = build_signed_tp101_gtr(
            source_id="por-node-2",
            source_type=SourceType.API,
            measurement_type=MeasurementType.CUSTOM,
            value=100.0,
            unit="bytes",
        )
        without = compute_eqs(record)
        with_binding = compute_eqs(record, binding_attestation_score=90)
        self.assertGreaterEqual(with_binding, without)

    def test_riv_scales_with_value(self) -> None:
        low = build_signed_tp101_gtr(
            source_id="a",
            source_type=SourceType.SENSOR,
            measurement_type=MeasurementType.CO2E,
            value=1.0,
            unit="kgCO2e",
        )
        high = build_signed_tp101_gtr(
            source_id="b",
            source_type=SourceType.SENSOR,
            measurement_type=MeasurementType.CO2E,
            value=100.0,
            unit="kgCO2e",
        )
        self.assertGreater(compute_riv(high), compute_riv(low))

    def test_score_verified_gtr_emits_valid_rfm(self) -> None:
        record = build_signed_tp101_gtr(
            source_id="por-node-3",
            source_type=SourceType.SENSOR,
            measurement_type=MeasurementType.ENERGY_KWH,
            value=10.0,
            unit="kWh",
        )
        gtr_hash = "a" * 64
        rfm = score_verified_gtr(
            record,
            gtr_hash=gtr_hash,
            binding_attestation_score=80,
            consensus_confidence=1.0,
            scoring_profile=ScoringProfile.PHASE1_ORACLE,
        )
        payload = rfm.to_dict()
        validate_por_payload(payload)
        self.assertEqual(payload["gtr_id"], record.gtr_id)
        self.assertEqual(payload["gtr_hash"], gtr_hash)
        self.assertEqual(payload["protocol_standard"], "TP-102")
        self.assertEqual(payload["scoring_profile"], "phase1_oracle")
        self.assertEqual(payload["consensus_confidence"], 1.0)
        self.assertGreaterEqual(payload["resonance_score"], 0)
        self.assertLessEqual(payload["resonance_score"], 100)


class ValidatorEligibilityTests(unittest.TestCase):
    def test_low_compliance_reduces_resonance(self) -> None:
        dimensions = ValidatorResonanceDimensions(
            r_env=0.8,
            r_gov=0.8,
            r_up=0.8,
            r_cmp=0.5,
        )
        profile = score_validator(
            validator_id="did:tegal:VALIDATOR003",
            validator_class=ValidatorClass.COMMUNITY,
            dimensions=dimensions,
            gtr_count_current_month=1,
        )
        self.assertLess(profile.resonance_score, 0.80)
        validate_por_payload(profile.to_dict())


if __name__ == "__main__":
    unittest.main()
