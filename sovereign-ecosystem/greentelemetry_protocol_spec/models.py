"""Type-safe models derived from greentelemetry-protocol-spec/schema.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SystemType(str, Enum):
    ZEEGATE_TELECOM = "ZEEGATE_TELECOM"
    BYTENERGY_UTILITY = "BYTENERGY_UTILITY"


class TelemetryValidationError(ValueError):
    """Raised when telemetry deviates from the unified specification."""


class EvidenceKind(str, Enum):
    GREETELEMETRY = "GREETELEMETRY"
    CDR = "CDR"
    AGGREGATE = "AGGREGATE"
    ASSET_RETIREMENT = "ASSET_RETIREMENT"


@dataclass(frozen=True, slots=True)
class ZkEvidence:
    scheme: str
    circuit_id: str
    evidence_kind: EvidenceKind
    public_inputs_hash: str
    commitment: str
    proof: str

    def to_dict(self) -> dict[str, str]:
        return {
            "scheme": self.scheme,
            "circuit_id": self.circuit_id,
            "evidence_kind": self.evidence_kind.value,
            "public_inputs_hash": self.public_inputs_hash,
            "commitment": self.commitment,
            "proof": self.proof,
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> ZkEvidence:
        try:
            return cls(
                scheme=str(raw["scheme"]),
                circuit_id=str(raw["circuit_id"]),
                evidence_kind=EvidenceKind(str(raw["evidence_kind"])),
                public_inputs_hash=str(raw["public_inputs_hash"]),
                commitment=str(raw["commitment"]),
                proof=str(raw["proof"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TelemetryValidationError(f"Malformed zk_evidence: {exc}") from exc


@dataclass(frozen=True, slots=True)
class Metrics:
    telecom_bandwidth_bytes: int | None = None
    energy_generation_kwh: float | None = None

    def to_dict(self) -> dict[str, int | float]:
        payload: dict[str, int | float] = {}
        if self.telecom_bandwidth_bytes is not None:
            payload["telecom_bandwidth_bytes"] = self.telecom_bandwidth_bytes
        if self.energy_generation_kwh is not None:
            payload["energy_generation_kwh"] = self.energy_generation_kwh
        return payload


@dataclass(frozen=True, slots=True)
class SovereignNodeTelemetry:
    node_id: str
    timestamp: int
    system_type: SystemType
    metrics: Metrics
    signature: str
    project_id: str | None = None
    binding_id: str | None = None
    zk_evidence: ZkEvidence | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "node_id": self.node_id,
            "timestamp": self.timestamp,
            "system_type": self.system_type.value,
            "metrics": self.metrics.to_dict(),
            "signature": self.signature,
        }
        if self.project_id is not None:
            payload["project_id"] = self.project_id
        if self.binding_id is not None:
            payload["binding_id"] = self.binding_id
        if self.zk_evidence is not None:
            payload["zk_evidence"] = self.zk_evidence.to_dict()
        return payload

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), separators=(",", ":"), sort_keys=True)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> SovereignNodeTelemetry:
        try:
            system_type = SystemType(payload["system_type"])
            raw_metrics = payload.get("metrics") or {}
            metrics = Metrics(
                telecom_bandwidth_bytes=raw_metrics.get("telecom_bandwidth_bytes"),
                energy_generation_kwh=raw_metrics.get("energy_generation_kwh"),
            )
            return cls(
                node_id=str(payload["node_id"]),
                timestamp=int(payload["timestamp"]),
                system_type=system_type,
                metrics=metrics,
                signature=str(payload["signature"]),
                project_id=payload.get("project_id"),
                binding_id=payload.get("binding_id"),
                zk_evidence=(
                    ZkEvidence.from_dict(payload["zk_evidence"])
                    if payload.get("zk_evidence")
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TelemetryValidationError(
                f"Malformed telemetry payload: {exc}"
            ) from exc


class SourceType(str, Enum):
    SENSOR = "SENSOR"
    MANUAL = "MANUAL"
    CERTIFIED_AUDITOR = "CERTIFIED_AUDITOR"
    API = "API"


class MeasurementType(str, Enum):
    CO2E = "CO2E"
    CH4 = "CH4"
    N2O = "N2O"
    ENERGY_KWH = "ENERGY_KWH"
    ENERGY_MJ = "ENERGY_MJ"
    WATER_M3 = "WATER_M3"
    BIODIVERSITY = "BIODIVERSITY"
    OFFSET_CREDIT = "OFFSET_CREDIT"
    CUSTOM = "CUSTOM"


class AttesterType(str, Enum):
    DEVICE = "DEVICE"
    OPERATOR = "OPERATOR"
    THIRD_PARTY = "THIRD_PARTY"
    REGULATORY = "REGULATORY"


@dataclass(frozen=True, slots=True)
class GeoPoint:
    latitude: float
    longitude: float
    altitude_m: float | None = None

    def to_dict(self) -> dict[str, float]:
        payload: dict[str, float] = {
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
        if self.altitude_m is not None:
            payload["altitude_m"] = self.altitude_m
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> GeoPoint:
        return cls(
            latitude=float(raw["latitude"]),
            longitude=float(raw["longitude"]),
            altitude_m=float(raw["altitude_m"]) if raw.get("altitude_m") is not None else None,
        )


@dataclass(frozen=True, slots=True)
class Attestation:
    attester_id: str
    attester_type: AttesterType
    signature: str
    timestamp: str
    confidence: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "attester_id": self.attester_id,
            "attester_type": self.attester_type.value,
            "signature": self.signature,
            "timestamp": self.timestamp,
        }
        if self.confidence is not None:
            payload["confidence"] = round(float(self.confidence), 2)
        if self.metadata:
            payload["metadata"] = self.metadata
        return payload

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> Attestation:
        confidence = raw.get("confidence")
        metadata = dict(raw.get("metadata") or {})
        if raw.get("legacy_sig") is True:
            metadata["legacy_sig"] = True
        return cls(
            attester_id=str(raw["attester_id"]),
            attester_type=AttesterType(str(raw["attester_type"])),
            signature=str(raw["signature"]),
            timestamp=str(raw["timestamp"]),
            confidence=float(confidence) if confidence is not None else None,
            metadata=metadata,
        )


@dataclass(frozen=True, slots=True)
class Tp101GreenTelemetryRecord:
    """Canonical TP-101 GreenTelemetry Record (GTR wire format)."""

    gtr_id: str
    source_id: str
    source_type: SourceType
    measurement_type: MeasurementType
    value: float
    unit: str
    timestamp: str
    attestations: tuple[Attestation, ...]
    schema_version: str = "1.0"
    location: GeoPoint | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    project_id: str | None = None
    binding_id: str | None = None
    zk_evidence: ZkEvidence | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "gtr_id": self.gtr_id,
            "source_id": self.source_id,
            "source_type": self.source_type.value,
            "measurement_type": self.measurement_type.value,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp,
            "attestations": [item.to_dict() for item in self.attestations],
            "schema_version": self.schema_version,
        }
        if self.location is not None:
            payload["location"] = self.location.to_dict()
        if self.metadata:
            payload["metadata"] = self.metadata
        if self.project_id is not None:
            payload["project_id"] = self.project_id
        if self.binding_id is not None:
            payload["binding_id"] = self.binding_id
        if self.zk_evidence is not None:
            payload["zk_evidence"] = self.zk_evidence.to_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> Tp101GreenTelemetryRecord:
        try:
            return cls(
                gtr_id=str(payload["gtr_id"]),
                source_id=str(payload["source_id"]),
                source_type=SourceType(str(payload["source_type"])),
                measurement_type=MeasurementType(str(payload["measurement_type"])),
                value=float(payload["value"]),
                unit=str(payload["unit"]),
                timestamp=str(payload["timestamp"]),
                attestations=tuple(
                    Attestation.from_dict(item) for item in payload["attestations"]
                ),
                schema_version=str(payload.get("schema_version", "1.0")),
                location=(
                    GeoPoint.from_dict(payload["location"])
                    if payload.get("location")
                    else None
                ),
                metadata=dict(payload.get("metadata") or {}),
                project_id=payload.get("project_id"),
                binding_id=payload.get("binding_id"),
                zk_evidence=(
                    ZkEvidence.from_dict(payload["zk_evidence"])
                    if payload.get("zk_evidence")
                    else None
                ),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise TelemetryValidationError(f"Malformed GTR payload: {exc}") from exc

