"""TP-101 security validations (timestamps, legacy signatures)."""

from __future__ import annotations

from datetime import UTC, datetime

from .models import TelemetryValidationError, Tp101GreenTelemetryRecord

ATTESTATION_WINDOW_SECONDS = 300  # ±5 minutes
MAX_RECORDS_PER_SOURCE_PER_HOUR = 10_000
ANCHOR_SLA_SECONDS = 60
RETENTION_YEARS = 7


def _parse_iso8601(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(UTC)


def assert_attestation_timestamps(record: Tp101GreenTelemetryRecord) -> None:
    """Attestation timestamp MUST be within ±5 minutes of measurement timestamp."""
    measurement_time = _parse_iso8601(record.timestamp)
    for attestation in record.attestations:
        attestation_time = _parse_iso8601(attestation.timestamp)
        delta = abs((attestation_time - measurement_time).total_seconds())
        if delta > ATTESTATION_WINDOW_SECONDS:
            raise TelemetryValidationError(
                f"attestation timestamp for {attestation.attester_id!r} is "
                f"{int(delta)}s from measurement (max {ATTESTATION_WINDOW_SECONDS}s)"
            )


def assert_ed25519_attestations(record: Tp101GreenTelemetryRecord) -> None:
    """Reject legacy signature algorithms unless explicitly flagged."""
    for attestation in record.attestations:
        metadata = attestation.metadata or {}
        if metadata.get("legacy_sig") is True:
            algorithm = str(metadata.get("algorithm", "")).upper()
            if algorithm not in {"RSA", "ECDSA_P256", "ECDSA-P256", "ECDSA"}:
                raise TelemetryValidationError(
                    "legacy_sig attestation must declare algorithm RSA or ECDSA_P256"
                )
            continue
        if len(attestation.signature) != 128:
            raise TelemetryValidationError(
                "non-legacy attestation signature must be 64-byte Ed25519 hex"
            )
