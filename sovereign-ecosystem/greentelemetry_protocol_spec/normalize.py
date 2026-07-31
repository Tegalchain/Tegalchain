"""Convert between legacy SovereignNodeTelemetry and canonical TP-101 GTR v1."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any, Literal

from .models import (
    AttesterType,
    MeasurementType,
    Metrics,
    SourceType,
    SovereignNodeTelemetry,
    SystemType,
    Tp101GreenTelemetryRecord,
)
from .signing import DEFAULT_HMAC_SECRET, sign_payload, unsigned_canonical_json
from .tp101_builder import attach_ed25519_attestation, iso8601_now

PayloadKind = Literal["legacy", "gtr_v1"]

GTR_SCHEMA_VERSION = "1.0"


def detect_payload_kind(payload: dict[str, Any]) -> PayloadKind:
    if payload.get("schema_version") == GTR_SCHEMA_VERSION and "gtr_id" in payload:
        return "gtr_v1"
    if "node_id" in payload and "system_type" in payload:
        return "legacy"
    raise ValueError("Unrecognized gretelemetry payload shape")


def unix_to_iso8601(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def iso8601_to_unix(timestamp: str) -> int:
    normalized = timestamp.replace("Z", "+00:00")
    return int(datetime.fromisoformat(normalized).timestamp())


def legacy_to_tp101(
    telemetry: SovereignNodeTelemetry,
    *,
    gtr_id: str | None = None,
    source_type: SourceType = SourceType.API,
    signing_secret: bytes | None = None,
) -> Tp101GreenTelemetryRecord:
    """Normalize legacy node envelope to canonical TP-101 GTR."""
    measurement_type, value, unit, metadata = _legacy_measurement(telemetry)
    measurement_time = unix_to_iso8601(telemetry.timestamp)
    unsigned = Tp101GreenTelemetryRecord(
        gtr_id=gtr_id or str(uuid.uuid4()),
        source_id=telemetry.node_id[:64],
        source_type=source_type,
        measurement_type=measurement_type,
        value=value,
        unit=unit,
        timestamp=measurement_time,
        attestations=(),
        schema_version=GTR_SCHEMA_VERSION,
        metadata=metadata,
        project_id=telemetry.project_id,
        binding_id=telemetry.binding_id,
        zk_evidence=telemetry.zk_evidence,
    )
    return attach_ed25519_attestation(
        unsigned,
        attester_id=telemetry.node_id[:64],
        attester_type=AttesterType.DEVICE,
        signing_secret=signing_secret,
        confidence=0.90,
        attestation_timestamp=measurement_time,
    )


def tp101_to_legacy(
    record: Tp101GreenTelemetryRecord,
    *,
    signing_secret: bytes | None = None,
) -> SovereignNodeTelemetry:
    """Project canonical GTR into legacy envelope for Phase 1 mint pipeline."""
    system_type, metrics = _tp101_to_legacy_metrics(record)
    secret = signing_secret if signing_secret is not None else DEFAULT_HMAC_SECRET
    unsigned = {
        "node_id": record.source_id,
        "timestamp": iso8601_to_unix(record.timestamp),
        "system_type": system_type.value,
        "metrics": metrics.to_dict(),
    }
    if record.project_id is not None:
        unsigned["project_id"] = record.project_id
    if record.binding_id is not None:
        unsigned["binding_id"] = record.binding_id
    if record.zk_evidence is not None:
        unsigned["zk_evidence"] = record.zk_evidence.to_dict()
    signature = sign_payload(unsigned_canonical_json(unsigned), secret)
    return SovereignNodeTelemetry(
        node_id=record.source_id,
        timestamp=iso8601_to_unix(record.timestamp),
        system_type=system_type,
        metrics=metrics,
        signature=signature,
        project_id=record.project_id,
        binding_id=record.binding_id,
        zk_evidence=record.zk_evidence,
    )


def _legacy_measurement(
    telemetry: SovereignNodeTelemetry,
) -> tuple[MeasurementType, float, str, dict[str, Any]]:
    metadata: dict[str, Any] = {
        "legacy_envelope": "sovereign_node_telemetry",
        "system_type": telemetry.system_type.value,
    }
    if telemetry.system_type is SystemType.BYTENERGY_UTILITY:
        kwh = telemetry.metrics.energy_generation_kwh or 0.0
        return MeasurementType.ENERGY_KWH, float(kwh), "kWh", metadata
    bytes_val = telemetry.metrics.telecom_bandwidth_bytes or 0
    metadata["legacy_metric"] = "telecom_bandwidth_bytes"
    return MeasurementType.CUSTOM, float(bytes_val), "bytes", metadata


def _tp101_to_legacy_metrics(
    record: Tp101GreenTelemetryRecord,
) -> tuple[SystemType, Metrics]:
    legacy_system = record.metadata.get("system_type")
    if legacy_system == SystemType.ZEEGATE_TELECOM.value:
        if record.measurement_type is MeasurementType.CUSTOM:
            return SystemType.ZEEGATE_TELECOM, Metrics(
                telecom_bandwidth_bytes=int(record.value)
            )
    if record.measurement_type is MeasurementType.ENERGY_KWH:
        return SystemType.BYTENERGY_UTILITY, Metrics(energy_generation_kwh=record.value)
    if legacy_system == SystemType.BYTENERGY_UTILITY.value:
        return SystemType.BYTENERGY_UTILITY, Metrics(energy_generation_kwh=record.value)
    if legacy_system == SystemType.ZEEGATE_TELECOM.value:
        return SystemType.ZEEGATE_TELECOM, Metrics(telecom_bandwidth_bytes=int(record.value))
    if record.measurement_type is MeasurementType.ENERGY_KWH:
        return SystemType.BYTENERGY_UTILITY, Metrics(energy_generation_kwh=record.value)
    return SystemType.ZEEGATE_TELECOM, Metrics(telecom_bandwidth_bytes=int(record.value))
