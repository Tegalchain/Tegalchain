"""Tests for TP-101 security validations."""

from __future__ import annotations

import sys
import unittest
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.models import (  # noqa: E402
    Attestation,
    AttesterType,
    MeasurementType,
    SourceType,
    TelemetryValidationError,
    Tp101GreenTelemetryRecord,
)
from greentelemetry_protocol_spec.security import (  # noqa: E402
    ATTESTATION_WINDOW_SECONDS,
    assert_attestation_timestamps,
    assert_ed25519_attestations,
)
from greentelemetry_protocol_spec.tp101_builder import (  # noqa: E402
    attach_ed25519_attestation,
    build_signed_tp101_gtr,
)
from greentelemetry_protocol_spec.validate import validate_gretelemetry  # noqa: E402


def _base_record(*, attestation_timestamp: str) -> Tp101GreenTelemetryRecord:
    measurement_time = "2026-07-26T12:00:00Z"
    unsigned = build_signed_tp101_gtr(
        source_id="bytenergy-node-1",
        source_type=SourceType.SENSOR,
        measurement_type=MeasurementType.ENERGY_KWH,
        value=1.0,
        unit="kWh",
        gtr_id=str(uuid.uuid4()),
        timestamp=measurement_time,
        attester_type=AttesterType.DEVICE,
    )
    return attach_ed25519_attestation(
        Tp101GreenTelemetryRecord(
            gtr_id=unsigned.gtr_id,
            source_id=unsigned.source_id,
            source_type=unsigned.source_type,
            measurement_type=unsigned.measurement_type,
            value=unsigned.value,
            unit=unsigned.unit,
            timestamp=measurement_time,
            attestations=(),
            schema_version=unsigned.schema_version,
        ),
        attester_id=unsigned.source_id,
        attester_type=AttesterType.DEVICE,
        attestation_timestamp=attestation_timestamp,
    )


class SecurityValidationTests(unittest.TestCase):
    def test_attestation_within_window_passes(self) -> None:
        record = _base_record(attestation_timestamp="2026-07-26T12:04:59Z")
        assert_attestation_timestamps(record)

    def test_attestation_outside_window_rejected(self) -> None:
        record = _base_record(attestation_timestamp="2026-07-26T12:06:01Z")
        with self.assertRaises(TelemetryValidationError) as ctx:
            assert_attestation_timestamps(record)
        self.assertIn(str(ATTESTATION_WINDOW_SECONDS), str(ctx.exception))

    def test_ed25519_requires_128_hex_chars(self) -> None:
        record = _base_record(attestation_timestamp="2026-07-26T12:00:00Z")
        bad = Tp101GreenTelemetryRecord(
            gtr_id=record.gtr_id,
            source_id=record.source_id,
            source_type=record.source_type,
            measurement_type=record.measurement_type,
            value=record.value,
            unit=record.unit,
            timestamp=record.timestamp,
            attestations=(
                Attestation(
                    attester_id=record.source_id,
                    attester_type=AttesterType.DEVICE,
                    signature="ab" * 32,
                    timestamp=record.timestamp,
                ),
            ),
            schema_version=record.schema_version,
        )
        with self.assertRaises(TelemetryValidationError):
            assert_ed25519_attestations(bad)

    def test_legacy_sig_allows_non_ed25519_length(self) -> None:
        record = Tp101GreenTelemetryRecord(
            gtr_id=str(uuid.uuid4()),
            source_id="legacy-device",
            source_type=SourceType.SENSOR,
            measurement_type=MeasurementType.CUSTOM,
            value=1.0,
            unit="bytes",
            timestamp="2026-07-26T12:00:00Z",
            attestations=(
                Attestation(
                    attester_id="legacy-device",
                    attester_type=AttesterType.DEVICE,
                    signature="legacy-rsa-signature",
                    timestamp="2026-07-26T12:00:00Z",
                    metadata={"legacy_sig": True, "algorithm": "RSA"},
                ),
            ),
            schema_version="1.0",
        )
        assert_ed25519_attestations(record)

    def test_validate_rejects_stale_attestation(self) -> None:
        payload = _base_record(attestation_timestamp="2026-07-26T12:00:00Z").to_dict()
        payload["attestations"][0]["timestamp"] = (
            datetime.now(tz=UTC) - timedelta(minutes=10)
        ).strftime("%Y-%m-%dT%H:%M:%SZ")
        with self.assertRaises(TelemetryValidationError):
            validate_gretelemetry(payload)


if __name__ == "__main__":
    unittest.main()
