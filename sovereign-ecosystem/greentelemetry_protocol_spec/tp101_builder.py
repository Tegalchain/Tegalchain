"""Build and sign canonical TP-101 GreenTelemetry Records (GTR v1)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from .models import (
    Attestation,
    AttesterType,
    GeoPoint,
    MeasurementType,
    SourceType,
    Tp101GreenTelemetryRecord,
)
from .gtr import GTR_SCHEMA_VERSION
from .signing import DEFAULT_HMAC_SECRET, sign_gtr_ed25519


def iso8601_now() -> str:
    return datetime.now(tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def attach_ed25519_attestation(
    record: Tp101GreenTelemetryRecord,
    *,
    attester_id: str,
    attester_type: AttesterType,
    signing_secret: bytes | None = None,
    confidence: float | None = None,
    attestation_timestamp: str | None = None,
) -> Tp101GreenTelemetryRecord:
    """Add an Ed25519 attestation over the GTR canonical hash."""
    unsigned_dict = record.to_dict()
    unsigned_dict["attestations"] = []
    secret = signing_secret if signing_secret is not None else DEFAULT_HMAC_SECRET
    attestation_time = attestation_timestamp or record.timestamp
    signature = sign_gtr_ed25519(unsigned_dict, secret)
    attestation = Attestation(
        attester_id=attester_id[:64],
        attester_type=attester_type,
        signature=signature,
        timestamp=attestation_time,
        confidence=confidence,
    )
    return Tp101GreenTelemetryRecord(
        gtr_id=record.gtr_id,
        source_id=record.source_id,
        source_type=record.source_type,
        measurement_type=record.measurement_type,
        value=record.value,
        unit=record.unit,
        timestamp=record.timestamp,
        attestations=record.attestations + (attestation,),
        schema_version=record.schema_version,
        location=record.location,
        metadata=record.metadata,
        project_id=record.project_id,
        binding_id=record.binding_id,
        zk_evidence=record.zk_evidence,
    )


def build_signed_tp101_gtr(
    *,
    source_id: str,
    source_type: SourceType,
    measurement_type: MeasurementType,
    value: float,
    unit: str,
    gtr_id: str | None = None,
    timestamp: str | None = None,
    location: GeoPoint | None = None,
    metadata: dict[str, Any] | None = None,
    project_id: str | None = None,
    binding_id: str | None = None,
    signing_secret: bytes | None = None,
    attester_type: AttesterType = AttesterType.DEVICE,
    confidence: float | None = 0.95,
) -> Tp101GreenTelemetryRecord:
    """Construct a signed TP-101 GTR ready for mint worker POST."""
    if len(source_id) > 64:
        raise ValueError("source_id must be string(64)")
    if len(unit) > 16 or not unit:
        raise ValueError("unit must be string(1..16)")

    measurement_time = timestamp or iso8601_now()
    unsigned = Tp101GreenTelemetryRecord(
        gtr_id=gtr_id or str(uuid.uuid4()),
        source_id=source_id,
        source_type=source_type,
        measurement_type=measurement_type,
        value=float(value),
        unit=unit,
        timestamp=measurement_time,
        attestations=(),
        schema_version=GTR_SCHEMA_VERSION,
        location=location,
        metadata=dict(metadata or {}),
        project_id=project_id,
        binding_id=binding_id,
    )
    return attach_ed25519_attestation(
        unsigned,
        attester_id=source_id,
        attester_type=attester_type,
        signing_secret=signing_secret,
        confidence=confidence,
        attestation_timestamp=measurement_time,
    )
