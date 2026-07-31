"""Translate validated gretelemetry into chain-neutral transaction proposals.

Builds ``TELEMETRY_MINT`` **block_candidate** payloads for the mint queue. This is a
pre-chain transaction proposal (sender, payload, timestamp) — not a committed
Tegalchain block. See docs/TEGALCHAIN.md (Transactions, Blocks).

Input is always schema-valid SovereignNodeTelemetry from the oracle path.
No dependency on Zeegate, Bytenergy, or other subsystem internals.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from greentelemetry_protocol_spec.models import SovereignNodeTelemetry, SystemType
from greentelemetry_protocol_spec.gtr import compute_legacy_hash
from greentelemetry_protocol_spec.validate import validate_telemetry

from .identity import NodeIdentity, resolve_node_identity
from .tegalid_gate import NodeBinding


@dataclass(frozen=True, slots=True)
class StateUpdate:
    state_key: str
    tegal_address: str
    payload: dict[str, Any]
    telemetry_hash: str


@dataclass(frozen=True, slots=True)
class MintResult:
    identity: NodeIdentity
    state_update: StateUpdate
    block_candidate: dict[str, Any]


def _telemetry_hash(telemetry: SovereignNodeTelemetry) -> str:
    return compute_legacy_hash(telemetry)


def _mint_payload(
    telemetry: SovereignNodeTelemetry,
    identity: NodeIdentity,
) -> dict[str, Any]:
    base = {
        "node_id": telemetry.node_id,
        "timestamp": telemetry.timestamp,
        "system_type": telemetry.system_type.value,
        "tegal_address": identity.tegal_address,
    }
    if telemetry.project_id is not None:
        base["project_id"] = telemetry.project_id
    if telemetry.binding_id is not None:
        base["binding_id"] = telemetry.binding_id
    if identity.tegalid_did is not None:
        base["tegalid_did"] = identity.tegalid_did

    if telemetry.system_type is SystemType.ZEEGATE_TELECOM:
        base["reward_basis"] = telemetry.metrics.telecom_bandwidth_bytes
        base["unit"] = "bytes"
    else:
        base["reward_basis"] = telemetry.metrics.energy_generation_kwh
        base["unit"] = "kwh"

    return base


def mint_from_telemetry(
    payload: dict[str, Any] | SovereignNodeTelemetry,
    binding: NodeBinding | None = None,
) -> MintResult:
    """
    Accept only schema-valid telemetry and produce a block-mint candidate.

    Raises TelemetryValidationError on any deviation from the unified spec.
    """
    telemetry = validate_telemetry(payload)
    identity = resolve_node_identity(telemetry.node_id, telemetry.system_type, binding)
    telemetry_hash = _telemetry_hash(telemetry)
    mint_payload = _mint_payload(telemetry, identity)

    state_update = StateUpdate(
        state_key=identity.state_key,
        tegal_address=identity.tegal_address,
        payload={
            **mint_payload,
            "last_telemetry_hash": telemetry_hash,
        },
        telemetry_hash=telemetry_hash,
    )

    block_candidate: dict[str, Any] = {
        "type": "TELEMETRY_MINT",
        "namespace": identity.mint_namespace,
        "signer": identity.tegal_address,
        "timestamp": telemetry.timestamp,
        "telemetry_hash": telemetry_hash,
        "state_key": identity.state_key,
        "mint_payload": mint_payload,
        "signature": telemetry.signature,
    }
    if identity.tegalid_did is not None:
        block_candidate["tegalid_did"] = identity.tegalid_did
    if identity.project_id is not None:
        block_candidate["project_id"] = identity.project_id
    if identity.binding_id is not None:
        block_candidate["binding_id"] = identity.binding_id
    if telemetry.zk_evidence is not None:
        block_candidate["zk_evidence"] = telemetry.zk_evidence.to_dict()
    block_candidate["auditrail_record_type"] = "GREETELEMETRY"

    return MintResult(
        identity=identity,
        state_update=state_update,
        block_candidate=block_candidate,
    )
