"""Tests for tegalchain TP-102 bridge (score_gtr_for_por)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: E402
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from proof_of_resonance_spec.validate import validate_por_payload  # noqa: E402
from tegalchain.por.score_gtr import score_gtr_for_por  # noqa: E402


class PorBridgeTests(unittest.TestCase):
    def test_edge_telecom_rfm_validates(self) -> None:
        tp101 = build_signed_tp101_gtr(
            source_id="zerocell-node-001",
            source_type=SourceType.API,
            measurement_type=MeasurementType.CUSTOM,
            value=1_048_576.0,
            unit="bytes",
            metadata={"system_type": "ZEEGATE_TELECOM", "legacy_metric": "telecom_bandwidth_bytes"},
        )
        rfm = score_gtr_for_por(tp101, gtr_hash="a" * 64)
        payload = rfm.to_dict()
        validate_por_payload(payload)
        self.assertEqual(payload["protocol_standard"], "TP-102")
        self.assertGreaterEqual(payload["resonance_score"], 0)
        self.assertLessEqual(payload["resonance_score"], 100)
        self.assertGreaterEqual(payload["eqs"], 0.4)
        self.assertLessEqual(payload["eqs"], 0.5)

    def test_cdr_evidence_higher_riv_than_zero_bytes(self) -> None:
        zero = build_signed_tp101_gtr(
            source_id="did:tegal:LABEDGE001",
            source_type=SourceType.API,
            measurement_type=MeasurementType.CUSTOM,
            value=0.0,
            unit="bytes",
            metadata={"evidence_kind": "CDR", "adapter": "zeegate_cdr"},
        )
        cdr = build_signed_tp101_gtr(
            source_id="did:tegal:LABEDGE001",
            source_type=SourceType.API,
            measurement_type=MeasurementType.CUSTOM,
            value=8192.0,
            unit="bytes",
            metadata={"evidence_kind": "CDR", "adapter": "zeegate_cdr"},
        )
        zero_rfm = score_gtr_for_por(zero, gtr_hash="b" * 64)
        cdr_rfm = score_gtr_for_por(cdr, gtr_hash="c" * 64)
        self.assertGreater(cdr_rfm.riv, zero_rfm.riv)
        self.assertGreaterEqual(cdr_rfm.resonance_score, zero_rfm.resonance_score)


if __name__ == "__main__":
    unittest.main()
