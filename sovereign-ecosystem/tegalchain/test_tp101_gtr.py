"""Tests for TP-101 canonical GTR schema and normalization."""

from __future__ import annotations

import sys
import time
import unittest
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import (  # noqa: E402
    AttesterType,
    MeasurementType,
    Metrics,
    SovereignNodeTelemetry,
    SystemType,
)
from greentelemetry_protocol_spec.tp101_builder import build_signed_tp101_gtr  # noqa: E402
from greentelemetry_protocol_spec.signing import verify_gtr_attestations  # noqa: E402
from greentelemetry_protocol_spec.validate import validate_gretelemetry  # noqa: E402


def _signed_legacy_energy() -> dict:
    from greentelemetry_protocol_spec.signing import sign_payload, unsigned_canonical_json

    unsigned = SovereignNodeTelemetry(
        node_id="bytenergy-node-1",
        timestamp=int(time.time()),
        system_type=SystemType.BYTENERGY_UTILITY,
        metrics=Metrics(energy_generation_kwh=12.5),
        signature="",
    )
    payload = unsigned.to_dict()
    payload["signature"] = sign_payload(unsigned_canonical_json(payload))
    return payload


def _signed_tp101_energy(*, gtr_id: str | None = None) -> dict:
    record = build_signed_tp101_gtr(
        source_id="bytenergy-node-1",
        source_type=__import__(
            "greentelemetry_protocol_spec.models", fromlist=["SourceType"]
        ).SourceType.API,
        measurement_type=MeasurementType.ENERGY_KWH,
        value=12.5,
        unit="kWh",
        gtr_id=gtr_id or str(uuid.uuid4()),
        metadata={"system_type": SystemType.BYTENERGY_UTILITY.value},
        attester_type=AttesterType.DEVICE,
        confidence=0.92,
    )
    return record.to_dict()


class Tp101GTRTests(unittest.TestCase):
    def test_legacy_energy_maps_to_energy_kwh(self) -> None:
        validated = validate_gretelemetry(_signed_legacy_energy())
        self.assertEqual(validated.tp101.measurement_type, MeasurementType.ENERGY_KWH)
        self.assertEqual(validated.tp101.unit, "kWh")
        self.assertEqual(validated.tp101.value, 12.5)
        self.assertEqual(validated.tp101.attestations[0].attester_type, AttesterType.DEVICE)
        self.assertEqual(len(validated.tp101.attestations[0].signature), 128)

    def test_canonical_gtr_round_trip(self) -> None:
        payload = _signed_tp101_energy()
        verify_gtr_attestations(payload)
        validated = validate_gretelemetry(payload)
        self.assertEqual(validated.kind, "gtr_v1")
        self.assertEqual(validated.tp101.measurement_type, MeasurementType.ENERGY_KWH)
        self.assertEqual(validated.legacy.system_type, SystemType.BYTENERGY_UTILITY)
        self.assertEqual(validated.legacy.metrics.energy_generation_kwh, 12.5)

    def test_gtr_requires_schema_version_1_0(self) -> None:
        payload = _signed_tp101_energy()
        payload["schema_version"] = "2.0"
        with self.assertRaises(Exception):
            validate_gretelemetry(payload)

    def test_rejects_invalid_measurement_unit(self) -> None:
        payload = _signed_tp101_energy()
        payload["unit"] = "invalid-unit-name-xx"
        with self.assertRaises(Exception):
            validate_gretelemetry(payload)

    def test_rejects_invalid_confidence(self) -> None:
        payload = _signed_tp101_energy()
        payload["attestations"][0]["confidence"] = 1.5
        with self.assertRaises(Exception):
            validate_gretelemetry(payload)


if __name__ == "__main__":
    unittest.main()
