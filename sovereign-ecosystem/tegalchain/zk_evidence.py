"""ZK evidence verification for final Greenledger telemetry / adapter output."""

from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from greentelemetry_protocol_spec.models import SovereignNodeTelemetry, ZkEvidence

HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEX_PATTERN = re.compile(r"^[0-9a-f]+$")


class ZkMode(str, Enum):
    OFF = "off"
    DEV = "dev"
    REQUIRED = "required"


class ZkEvidenceError(ValueError):
    """Raised when zk_evidence is missing or invalid for the configured ZK mode."""


def get_zk_mode() -> ZkMode:
    raw = os.environ.get("TEGALCHAIN_ZK_MODE", ZkMode.OFF.value).lower()
    try:
        return ZkMode(raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid TEGALCHAIN_ZK_MODE={raw!r}; use off, dev, or required"
        ) from exc


def public_inputs_canonical(payload: dict[str, Any]) -> str:
    """Canonical JSON for ZK public inputs — envelope without signature or zk_evidence."""
    unsigned = {
        key: value
        for key, value in payload.items()
        if key not in ("signature", "zk_evidence")
    }
    return json.dumps(unsigned, separators=(",", ":"), sort_keys=True)


def public_inputs_hash(payload: dict[str, Any]) -> str:
    return hashlib.sha256(public_inputs_canonical(payload).encode()).hexdigest()


def _validate_zk_shape(zk: ZkEvidence) -> None:
    if not HEX64.match(zk.public_inputs_hash):
        raise ZkEvidenceError("zk_evidence.public_inputs_hash must be 64 hex chars")
    if not zk.commitment or not HEX_PATTERN.match(zk.commitment):
        raise ZkEvidenceError("zk_evidence.commitment must be lowercase hex")
    if not zk.proof or not HEX_PATTERN.match(zk.proof):
        raise ZkEvidenceError("zk_evidence.proof must be lowercase hex")


def verify_zk_evidence(
    telemetry: SovereignNodeTelemetry | dict[str, Any],
) -> ZkEvidence | None:
    """
    Verify ZK binding on final gretelemetry destined for the Greenledger.

    Full cryptographic verification happens on-chain; the oracle checks structure
    and public_inputs_hash binding in dev/required modes.
    """
    mode = get_zk_mode()
    if mode is ZkMode.OFF:
        return None

    if isinstance(telemetry, SovereignNodeTelemetry):
        payload = telemetry.to_dict()
        zk = telemetry.zk_evidence
    else:
        payload = telemetry
        raw_zk = payload.get("zk_evidence")
        zk = ZkEvidence.from_dict(raw_zk) if raw_zk else None

    if zk is None:
        if mode is ZkMode.REQUIRED:
            raise ZkEvidenceError("zk_evidence required when TEGALCHAIN_ZK_MODE=required")
        return None

    _validate_zk_shape(zk)

    if mode is ZkMode.REQUIRED and zk.scheme == "placeholder-dev":
        raise ZkEvidenceError("placeholder-dev scheme not allowed when ZK mode is required")

    expected_hash = public_inputs_hash(payload)
    if zk.public_inputs_hash != expected_hash:
        raise ZkEvidenceError(
            "zk_evidence.public_inputs_hash does not match canonical public inputs"
        )

    # Production: invoke gnark / chain verifier here using zk.proof + circuit_id
    return zk
