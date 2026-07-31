"""Tegalid identity gate for gretelemetry mint eligibility.

Tegalchain does not integrate with external subsystems directly. This module
gates signed gretelemetry at the oracle ingress using tegalid bindings and the
Greenledger project registry.
"""

from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

from greentelemetry_protocol_spec.models import SovereignNodeTelemetry, SystemType
from greentelemetry_protocol_spec.signing import DEFAULT_HMAC_SECRET

from .project_registry import assert_project_registered

DID_PREFIX = "did:tegal:"
DID_PATTERN = re.compile(r"^did:tegal:[A-Za-z0-9_-]+$")

ROOT = Path(__file__).resolve().parent
DEFAULT_BINDINGS_FILE = ROOT / "data" / "tegalid_bindings.json"


class IdentityMode(str, Enum):
    DEV = "dev"
    TEGALID = "tegalid"


class TegalidGateError(PermissionError):
    """Raised when telemetry fails tegalid identity or mint eligibility checks."""


class BindingStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"


class KycLevel(str, Enum):
    NONE = "NONE"
    BASIC = "BASIC"
    VERIFIED = "VERIFIED"


@dataclass(frozen=True, slots=True)
class NodeBinding:
    did: str
    project_id: str
    system_type: SystemType
    binding_id: str
    kyc_level: KycLevel
    attestation_score: int
    status: BindingStatus
    mint_eligible: bool
    tegal_address: str
    telemetry_key_id: str
    telemetry_hmac_secret: bytes
    sip_user: str
    sip_domain: str
    sip_credential_commitment: str
    metadata_uri: str = ""
    expires_at: int = 0

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> NodeBinding:
        secret = raw.get("telemetry_hmac_secret") or raw.get("telemetry_hmac_secret_hex")
        if isinstance(secret, str):
            telemetry_hmac_secret = bytes.fromhex(secret)
        elif isinstance(secret, bytes):
            telemetry_hmac_secret = secret
        else:
            raise ValueError("telemetry_hmac_secret or telemetry_hmac_secret_hex required")

        return cls(
            did=str(raw["did"]),
            project_id=str(raw["project_id"]),
            system_type=SystemType(str(raw["system_type"])),
            binding_id=str(raw["binding_id"]),
            kyc_level=KycLevel(str(raw.get("kyc_level", "VERIFIED"))),
            attestation_score=int(raw.get("attestation_score", 0)),
            status=BindingStatus(str(raw.get("status", "ACTIVE"))),
            mint_eligible=bool(raw.get("mint_eligible", False)),
            tegal_address=str(raw["tegal_address"]),
            telemetry_key_id=str(raw.get("telemetry_key_id", "default")),
            telemetry_hmac_secret=telemetry_hmac_secret,
            sip_user=str(raw.get("sip_user", "")),
            sip_domain=str(raw.get("sip_domain", "")),
            sip_credential_commitment=str(raw.get("sip_credential_commitment", "")),
            metadata_uri=str(raw.get("metadata_uri", "")),
            expires_at=int(raw.get("expires_at", 0)),
        )


class BindingStore:
    """Load tegalid NodeBindings from JSON cache (lab) or future chain REST."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._bindings: dict[tuple[str, str], NodeBinding] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            self._bindings = {}
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        entries = data.get("bindings", data if isinstance(data, list) else [])
        loaded: dict[tuple[str, str], NodeBinding] = {}
        for entry in entries:
            binding = NodeBinding.from_dict(entry)
            loaded[(binding.did, binding.system_type.value)] = binding
        self._bindings = loaded

    def reload(self) -> None:
        self._load()

    def get(self, did: str, system_type: SystemType) -> NodeBinding | None:
        return self._bindings.get((did, system_type.value))

    def all_bindings(self) -> list[NodeBinding]:
        return list(self._bindings.values())


def get_identity_mode() -> IdentityMode:
    raw = os.environ.get("TEGALCHAIN_IDENTITY_MODE", IdentityMode.DEV.value).lower()
    try:
        return IdentityMode(raw)
    except ValueError as exc:
        raise ValueError(
            f"Invalid TEGALCHAIN_IDENTITY_MODE={raw!r}; use dev or tegalid"
        ) from exc


def get_bindings_file() -> Path:
    return Path(os.environ.get("TEGALID_BINDINGS_FILE", str(DEFAULT_BINDINGS_FILE)))


def is_tegalid_did(node_id: str) -> bool:
    return bool(DID_PATTERN.match(node_id))


def resolve_binding_store() -> BindingStore:
    path = get_bindings_file()
    if not path.is_file():
        example = path.parent / "tegalid_bindings.example.json"
        if example.is_file():
            path = example
    return BindingStore(path)


def resolve_ingest_signing_secret(
    payload: dict[str, Any],
    kind: str,
    binding: NodeBinding | None,
) -> bytes:
    """Resolve HMAC/Ed25519 verification secret at oracle ingress.

    In tegalid mode ``binding`` is always set. In dev mode, tegalid-bound GTRs
    (e.g. CDR adapter → ``did:tegal:…``) still verify against the binding secret
    when a matching entry exists in the local bindings cache.
    """
    if binding is not None:
        return binding.telemetry_hmac_secret
    if kind != "gtr_v1":
        return DEFAULT_HMAC_SECRET
    source_id = str(payload.get("source_id", ""))
    if not is_tegalid_did(source_id):
        return DEFAULT_HMAC_SECRET
    metadata = payload.get("metadata") or {}
    try:
        system_type = SystemType(str(metadata.get("system_type", "ZEEGATE_TELECOM")))
    except ValueError:
        system_type = SystemType.ZEEGATE_TELECOM
    found = resolve_binding_store().get(source_id, system_type)
    if found is not None:
        return found.telemetry_hmac_secret
    return DEFAULT_HMAC_SECRET


def _assert_binding_active(binding: NodeBinding) -> None:
    if binding.status is not BindingStatus.ACTIVE:
        raise TegalidGateError(f"Binding status is {binding.status.value}, not ACTIVE")
    if binding.expires_at and time.time() >= binding.expires_at:
        raise TegalidGateError("Binding has expired")
    if not binding.mint_eligible:
        raise TegalidGateError("Binding is not mint eligible per tegalid policy")


def assert_mint_eligible(
    telemetry: SovereignNodeTelemetry | dict[str, Any],
    store: BindingStore | None = None,
) -> NodeBinding | None:
    """
    Enforce tegalid identity lock when identity mode is tegalid.

    Returns NodeBinding when mode is tegalid; None in dev mode.
    """
    if get_identity_mode() is IdentityMode.DEV:
        return None

    if isinstance(telemetry, SovereignNodeTelemetry):
        node_id = telemetry.node_id
        system_type = telemetry.system_type
        project_id = telemetry.project_id
        binding_id = telemetry.binding_id
    else:
        node_id = str(telemetry["node_id"])
        system_type = SystemType(str(telemetry["system_type"]))
        project_id = telemetry.get("project_id")
        binding_id = telemetry.get("binding_id")

    if not is_tegalid_did(node_id):
        raise TegalidGateError(
            f"node_id must be a tegalid DID ({DID_PREFIX}…), got {node_id!r}"
        )

    store = store or resolve_binding_store()
    binding = store.get(node_id, system_type)
    if binding is None:
        raise TegalidGateError(
            f"No tegalid NodeBinding for {node_id} / {system_type.value}"
        )

    _assert_binding_active(binding)

    try:
        assert_project_registered(binding.project_id, system_type)
    except ValueError as exc:
        raise TegalidGateError(str(exc)) from exc

    if project_id is not None:
        if project_id != binding.project_id:
            raise TegalidGateError(
                f"project_id mismatch: payload={project_id!r} binding={binding.project_id!r}"
            )
        try:
            assert_project_registered(project_id, system_type)
        except ValueError as exc:
            raise TegalidGateError(str(exc)) from exc
    if binding_id is not None and binding_id != binding.binding_id:
        raise TegalidGateError(
            f"binding_id mismatch: payload={binding_id!r} binding={binding.binding_id!r}"
        )

    return binding
