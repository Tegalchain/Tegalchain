"""Tests for TP-101 GreenTelemetry Record (GTR) bridge."""

from __future__ import annotations

import sys
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.gtr import (  # noqa: E402
    GreenTelemetryRecord,
    ReportingMode,
    TP101_STANDARD_ID,
    compute_gtr_hash,
)
from greentelemetry_protocol_spec.models import Metrics, SovereignNodeTelemetry, SystemType  # noqa: E402
from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_gretelemetry  # noqa: E402
from tegalchain.gtr import GTRConsumer, build_ledger_bound_gtr  # noqa: E402
from tegalchain.mint import mint_from_telemetry  # noqa: E402


def _signed_telemetry() -> SovereignNodeTelemetry:
    unsigned = SovereignNodeTelemetry(
        node_id="test-node-gtr",
        timestamp=int(time.time()),
        system_type=SystemType.ZEEGATE_TELECOM,
        metrics=Metrics(telecom_bandwidth_bytes=1024),
        signature="",
    )
    canonical = unsigned_canonical_json(unsigned.to_dict())
    return SovereignNodeTelemetry(
        node_id=unsigned.node_id,
        timestamp=unsigned.timestamp,
        system_type=unsigned.system_type,
        metrics=unsigned.metrics,
        signature=sign_payload(canonical),
    )


class GTRTests(unittest.TestCase):
    def test_legacy_normalizes_to_tp101(self) -> None:
        telemetry = _signed_telemetry()
        validated = validate_gretelemetry(telemetry.to_dict())
        self.assertEqual(validated.kind, "legacy")
        self.assertEqual(validated.tp101.source_id, telemetry.node_id)
        self.assertEqual(validated.tp101.measurement_type.value, "CUSTOM")
        self.assertEqual(validated.tp101.unit, "bytes")

    def test_ledger_bound_gtr_enriches_block_candidate(self) -> None:
        telemetry = _signed_telemetry()
        validated = validate_gretelemetry(telemetry.to_dict())
        mint_result = mint_from_telemetry(validated.legacy)
        bound = build_ledger_bound_gtr(
            mint_result,
            validated,
            reporting_mode=ReportingMode.BATCH,
        )
        self.assertEqual(bound.block_candidate["gtr_id"], validated.tp101.gtr_id)
        self.assertEqual(
            bound.block_candidate["gtr_hash"],
            compute_gtr_hash(validated.tp101),
        )
        self.assertEqual(bound.block_candidate["protocol_standard"], TP101_STANDARD_ID)
        self.assertEqual(bound.block_candidate["schema_version"], "1.0")
        self.assertIn("tp101_record", bound.block_candidate)
        self.assertIn("tp102_rfm", bound.block_candidate)
        self.assertEqual(bound.block_candidate["tp102_rfm"]["protocol_standard"], "TP-102")
        self.assertIn(GTRConsumer.GREEN_LEDGER, bound.consumers)

    def test_consumer_metadata_routes_tp_standards(self) -> None:
        telemetry = _signed_telemetry()
        validated = validate_gretelemetry(telemetry.to_dict())
        mint_result = mint_from_telemetry(validated.legacy)
        bound = build_ledger_bound_gtr(mint_result, validated)
        meta = bound.consumer_metadata()
        self.assertEqual(meta["protocol_standard"], TP101_STANDARD_ID)
        self.assertEqual(meta["schema_version"], "1.0")
        self.assertIn("TP-103", meta["consumers"])
        self.assertIn("TP-102", meta["consumers"])
        self.assertIn("TP-106", meta["consumers"])
        self.assertGreaterEqual(meta["trust_score"], 0.0)
        self.assertEqual(meta["attestation_count"], 1)
        por = meta["consumers"]["TP-102"]
        self.assertIn("rfm", por)
        self.assertEqual(por["rfm"]["protocol_standard"], "TP-102")
        self.assertIn("eqs", por["rfm"])
        self.assertIn("riv", por["rfm"])
        self.assertIn("resonance_score", por["rfm"])


if __name__ == "__main__":
    unittest.main()
