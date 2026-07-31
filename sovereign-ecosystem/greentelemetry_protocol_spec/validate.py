"""JSON Schema validation against greentelemetry-protocol-spec/schema.json."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import (
    SovereignNodeTelemetry,
    TelemetryValidationError,
    Tp101GreenTelemetryRecord,
)
from .normalize import (
    PayloadKind,
    detect_payload_kind,
    legacy_to_tp101,
    tp101_to_legacy,
)
from .units import assert_measurement_unit
from .security import assert_attestation_timestamps, assert_ed25519_attestations

try:
    import jsonschema
except ImportError:  # pragma: no cover - runtime guard for minimal installs
    jsonschema = None  # type: ignore[assignment]


SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "greentelemetry-protocol-spec"
    / "schema.json"
)


@dataclass(frozen=True, slots=True)
class ValidatedGreTelemetry:
    """Schema-valid payload with canonical TP-101 GTR and legacy projection."""

    kind: PayloadKind
    tp101: Tp101GreenTelemetryRecord
    legacy: SovereignNodeTelemetry
    raw: dict[str, Any]


@lru_cache(maxsize=1)
def load_schema() -> dict[str, Any]:
    with SCHEMA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def _validate_schema(data: dict[str, Any]) -> None:
    if jsonschema is None:
        raise RuntimeError(
            "jsonschema is required for protocol validation; install with: pip install jsonschema"
        )
    schema = load_schema()
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as exc:
        raise TelemetryValidationError(
            f"Schema violation at {list(exc.absolute_path)}: {exc.message}"
        ) from exc


def _assert_tp101_domain(record: Tp101GreenTelemetryRecord) -> None:
    if record.schema_version != "1.0":
        raise TelemetryValidationError(
            f"schema_version must be 1.0 for TP-101 GTR, got {record.schema_version!r}"
        )
    if not record.attestations:
        raise TelemetryValidationError("GTR requires at least one attestation")
    for attestation in record.attestations:
        if attestation.confidence is not None and not 0.0 <= attestation.confidence <= 1.0:
            raise TelemetryValidationError("attestation confidence must be between 0.00 and 1.00")
    assert_measurement_unit(record.measurement_type, record.unit)
    assert_attestation_timestamps(record)
    assert_ed25519_attestations(record)


def validate_gretelemetry(
    payload: dict[str, Any] | SovereignNodeTelemetry | Tp101GreenTelemetryRecord,
    *,
    signing_secret: bytes | None = None,
) -> ValidatedGreTelemetry:
    """Validate payload and return canonical GTR plus legacy projection."""
    if isinstance(payload, SovereignNodeTelemetry):
        data = payload.to_dict()
    elif isinstance(payload, Tp101GreenTelemetryRecord):
        data = payload.to_dict()
    else:
        data = payload

    _validate_schema(data)
    kind = detect_payload_kind(data)

    if kind == "gtr_v1":
        tp101 = Tp101GreenTelemetryRecord.from_dict(data)
        _assert_tp101_domain(tp101)
        legacy = tp101_to_legacy(tp101, signing_secret=signing_secret)
    else:
        legacy = SovereignNodeTelemetry.from_dict(data)
        tp101 = legacy_to_tp101(legacy, signing_secret=signing_secret)

    return ValidatedGreTelemetry(kind=kind, tp101=tp101, legacy=legacy, raw=data)


def validate_telemetry(
    payload: dict[str, Any] | SovereignNodeTelemetry,
) -> SovereignNodeTelemetry:
    """Validate payload against schema.json; legacy return type for Phase 1 callers."""
    return validate_gretelemetry(payload).legacy
