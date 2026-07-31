"""Map gretelemetry node_id to chain-facing identity (via tegalid binding or dev stub).

Identity reaches Tegalchain only through the gretelemetry oracle — never from
subsystem-specific code paths.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from greentelemetry_protocol_spec.models import SystemType

from .tegalid_gate import IdentityMode, NodeBinding, get_identity_mode


@dataclass(frozen=True, slots=True)
class NodeIdentity:
    """On-chain identity derived from a sovereign node_id."""

    node_id: str
    system_type: SystemType
    tegal_address: str
    state_key: str
    tegalid_did: str | None = None
    project_id: str | None = None
    binding_id: str | None = None

    @property
    def mint_namespace(self) -> str:
        return f"tegal:{self.system_type.value.lower()}"


def resolve_node_identity(
    node_id: str,
    system_type: SystemType,
    binding: NodeBinding | None = None,
) -> NodeIdentity:
    """
    Map a node into Tegalchain address space.

    tegalid mode: requires NodeBinding (tegal_address from Greenledger).
    dev mode: deterministic SHA-256 placeholder for local lab.
    """
    if not node_id or not node_id.strip():
        raise ValueError("node_id must be a non-empty string")

    mode = get_identity_mode()
    if mode is IdentityMode.TEGALID:
        if binding is None:
            raise ValueError("tegalid mode requires a NodeBinding")
        namespace = f"tegal:{system_type.value}"
        digest = hashlib.sha256(f"{binding.did}:{binding.project_id}".encode()).hexdigest()
        state_key = f"{namespace}/binding/{binding.binding_id}/{digest[:16]}"
        return NodeIdentity(
            node_id=node_id,
            system_type=system_type,
            tegal_address=binding.tegal_address,
            state_key=state_key,
            tegalid_did=binding.did,
            project_id=binding.project_id,
            binding_id=binding.binding_id,
        )

    namespace = f"tegal:{system_type.value}"
    digest = hashlib.sha256(f"{namespace}:{node_id}".encode()).hexdigest()
    tegal_address = f"TEGAL-{digest[:40].upper()}"
    state_key = f"{namespace}/state/{digest}"

    return NodeIdentity(
        node_id=node_id,
        system_type=system_type,
        tegal_address=tegal_address,
        state_key=state_key,
    )
