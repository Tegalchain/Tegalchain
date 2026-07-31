"""Tests for Zeegate telemetry client GTR v1 emission."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import MeasurementType, SourceType  # noqa: E402
from greentelemetry_protocol_spec.signing import verify_gtr_attestations  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_gretelemetry  # noqa: E402
from integrations.zeegate_telemetry.client import ZeegateClient  # noqa: E402


class ZeegateGTRClientTests(unittest.TestCase):
    def test_build_gtr_v1_telecom_custom_bytes(self) -> None:
        client = ZeegateClient(node_id="zerocell-node-001")
        record = client.build_gtr_v1(2048, source_type=SourceType.SENSOR)
        self.assertEqual(record.source_id, "zerocell-node-001")
        self.assertEqual(record.source_type, SourceType.SENSOR)
        self.assertEqual(record.measurement_type, MeasurementType.CUSTOM)
        self.assertEqual(record.unit, "bytes")
        self.assertEqual(record.value, 2048.0)
        self.assertEqual(record.schema_version, "1.0")
        self.assertEqual(record.metadata["legacy_metric"], "telecom_bandwidth_bytes")
        self.assertEqual(record.attestations[0].attester_type.value, "DEVICE")
        self.assertEqual(len(record.attestations[0].signature), 128)

    def test_gtr_v1_validates_and_verifies(self) -> None:
        client = ZeegateClient(node_id="zerocell-node-001")
        payload = client.build_gtr_v1(512).to_dict()
        verify_gtr_attestations(payload)
        validated = validate_gretelemetry(payload)
        self.assertEqual(validated.kind, "gtr_v1")
        self.assertEqual(validated.tp101.gtr_id, payload["gtr_id"])


if __name__ == "__main__":
    unittest.main()
