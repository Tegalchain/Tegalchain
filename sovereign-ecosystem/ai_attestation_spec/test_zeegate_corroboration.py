"""Tests for Zeegate CDR ↔ bandwidth corroboration."""

from __future__ import annotations

import unittest
from pathlib import Path

from ai_attestation_spec.attestation import (
    build_third_party_attestation,
    tp108_metadata_from_corroboration,
)
from ai_attestation_spec.keys import DEFAULT_MODEL_PROFILE
from ai_attestation_spec.zeegate_corroboration import (
    CorroborationVerdict,
    corroborate_from_fixture,
    evaluate_corroboration,
    load_cdr_billsec,
)
from greentelemetry_protocol_spec.signing import verify_gtr_ed25519_attestation
from ai_attestation_spec.keys import LAB_AI_ATTESTER_SECRET


FIXTURE = Path(__file__).resolve().parents[1] / "zeegate-cloud" / "cdr_adapter" / "fixtures" / "sample_cdr.csv"


class TestZeegateCorroboration(unittest.TestCase):
    def test_lab_fixture_passes_with_1mib(self) -> None:
        tp101 = {
            "gtr_id": "5d8528c0-ce18-4a13-9be9-59fedb095049",
            "source_id": "did:tegal:LABEDGE001",
            "value": 1048576,
            "unit": "bytes",
            "metadata": {"legacy_metric": "telecom_bandwidth_bytes"},
        }
        result = corroborate_from_fixture(tp101, FIXTURE)
        self.assertEqual(result.verdict, CorroborationVerdict.PASS)
        self.assertEqual(result.billsec, 85)

    def test_warn_band(self) -> None:
        verdict, _, _ = evaluate_corroboration(1048576 * 3, 85)
        self.assertEqual(verdict, CorroborationVerdict.WARN)

    def test_signed_attestation_verifies(self) -> None:
        tp101 = {
            "gtr_id": "5d8528c0-ce18-4a13-9be9-59fedb095049",
            "source_id": "did:tegal:LABEDGE001",
            "value": 1048576,
            "unit": "bytes",
            "metadata": {"legacy_metric": "telecom_bandwidth_bytes"},
            "attestations": [{"attester_type": "DEVICE", "attester_id": "did:tegal:LABEDGE001"}],
        }
        result = corroborate_from_fixture(tp101, FIXTURE)
        tp108 = tp108_metadata_from_corroboration(result, model_profile=DEFAULT_MODEL_PROFILE)
        attestation = build_third_party_attestation(tp101, tp108=tp108, confidence=0.9)
        unsigned = {key: value for key, value in tp101.items() if key != "attestations"}
        verify_gtr_ed25519_attestation(unsigned, attestation, LAB_AI_ATTESTER_SECRET)

    def test_load_cdr_billsec(self) -> None:
        billsec, cdr_hash = load_cdr_billsec(FIXTURE)
        self.assertEqual(billsec, 85)
        self.assertEqual(len(cdr_hash), 64)


if __name__ == "__main__":
    unittest.main()
