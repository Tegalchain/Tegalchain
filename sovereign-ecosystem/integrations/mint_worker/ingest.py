"""Shared gretelemetry / GTR ingestion pipeline for mint worker transports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from greentelemetry_protocol_spec.gtr import ReportingMode
from greentelemetry_protocol_spec.models import TelemetryValidationError
from greentelemetry_protocol_spec.normalize import detect_payload_kind
from greentelemetry_protocol_spec.security import MAX_RECORDS_PER_SOURCE_PER_HOUR
from greentelemetry_protocol_spec.signing import (
    SignatureVerificationError,
    verify_gtr_attestations,
    verify_telemetry_signature,
)
from greentelemetry_protocol_spec.validate import validate_gretelemetry
from tegalchain.anchor import build_on_chain_anchor
from tegalchain.endorsement import Endorsement, ORACLE_PEER_ID, attach_endorsements
from tegalchain.gtr import build_ledger_bound_gtr
from tegalchain.mint import mint_from_telemetry
from tegalchain.queue.store import MintQueueRecord, MintQueueStore
from tegalchain.source_registry import SourceRegistryError, assert_source_registered, require_source_registry
from tegalchain.tegalid_gate import (
    NodeBinding,
    TegalidGateError,
    assert_mint_eligible,
    resolve_ingest_signing_secret,
)
from tegalchain.zk_evidence import ZkEvidenceError, verify_zk_evidence


class IngestError(Exception):
    """Base ingestion failure with HTTP status hint."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(frozen=True, slots=True)
class IngestResult:
    queue_id: int
    gtr_id: str
    ledger_ref: str | None
    status: str
    telemetry: dict[str, Any]
    identity: dict[str, Any]
    state_update: dict[str, Any]
    block_candidate: dict[str, Any]
    gtr: dict[str, Any]
    on_chain_anchor: dict[str, Any]


def tegalid_probe_payload(payload: dict[str, Any], kind: str) -> dict[str, Any]:
    if kind != "gtr_v1":
        return payload
    metadata = payload.get("metadata") or {}
    probe: dict[str, Any] = {
        "node_id": payload["source_id"],
        "system_type": metadata.get("system_type", "ZEEGATE_TELECOM"),
    }
    if payload.get("project_id") is not None:
        probe["project_id"] = payload["project_id"]
    if payload.get("binding_id") is not None:
        probe["binding_id"] = payload["binding_id"]
    return probe


def source_id_from_payload(payload: dict[str, Any], kind: str) -> str:
    if kind == "gtr_v1":
        return str(payload["source_id"])
    return str(payload["node_id"])


def ingest_payload(
    store: MintQueueStore,
    payload: dict[str, Any],
    *,
    reporting_mode: ReportingMode = ReportingMode.STREAM,
) -> IngestResult:
    """Validate, gate, anchor-enqueue a legacy envelope or canonical GTR."""
    try:
        kind = detect_payload_kind(payload)
        source_id = source_id_from_payload(payload, kind)
        if require_source_registry():
            assert_source_registered(source_id)
        store.check_and_increment_source_rate(
            source_id,
            max_per_hour=MAX_RECORDS_PER_SOURCE_PER_HOUR,
        )
        binding: NodeBinding | None = assert_mint_eligible(
            tegalid_probe_payload(payload, kind)
        )
        secret = resolve_ingest_signing_secret(payload, kind, binding)
        if kind == "gtr_v1":
            verify_gtr_attestations(payload, secret)
        else:
            verify_telemetry_signature(payload, secret)
        validated = validate_gretelemetry(payload, signing_secret=secret)
        verify_zk_evidence(validated.legacy)
        result = mint_from_telemetry(validated.legacy, binding)
        bound_gtr = build_ledger_bound_gtr(
            result,
            validated,
            binding=binding,
            reporting_mode=reporting_mode,
        )
    except SourceRegistryError as exc:
        raise IngestError(str(exc), 403) from exc
    except ZkEvidenceError as exc:
        raise IngestError(str(exc), 422) from exc
    except TegalidGateError as exc:
        raise IngestError(str(exc), 403) from exc
    except SignatureVerificationError as exc:
        raise IngestError(str(exc), 401) from exc
    except TelemetryValidationError as exc:
        raise IngestError(str(exc), 422) from exc
    except ValueError as exc:
        raise IngestError(str(exc), 429 if "rate limit" in str(exc) else 400) from exc

    on_chain_anchor = build_on_chain_anchor(validated.tp101)
    identity = result.identity
    state = result.state_update
    identity_payload = {
        "node_id": identity.node_id,
        "system_type": identity.system_type.value,
        "tegal_address": identity.tegal_address,
        "state_key": identity.state_key,
        "mint_namespace": identity.mint_namespace,
    }
    state_payload = {
        "state_key": state.state_key,
        "tegal_address": state.tegal_address,
        "payload": state.payload,
        "telemetry_hash": state.telemetry_hash,
    }
    block_candidate = attach_endorsements(
        bound_gtr.block_candidate,
        [Endorsement(peer=ORACLE_PEER_ID, read_write_set_hash=state.telemetry_hash)],
    )
    block_candidate["on_chain_anchor"] = on_chain_anchor.to_dict()
    block_candidate["accepted_at"] = datetime.now(tz=UTC).isoformat()
    gtr_id = str(bound_gtr.tp101.gtr_id)
    queue_id = store.enqueue(
        telemetry_hash=state.telemetry_hash,
        block_candidate=block_candidate,
        state_update=state_payload,
        identity=identity_payload,
        gtr_id=gtr_id,
    )
    queued = store.fetch_by_id(queue_id)
    ledger_ref = queued.submit_ref if queued and queued.status == "submitted" else None
    status = queued.status if queued else "pending"
    return IngestResult(
        queue_id=queue_id,
        gtr_id=gtr_id,
        ledger_ref=ledger_ref,
        status=status,
        telemetry=payload,
        identity=identity_payload,
        state_update=state_payload,
        block_candidate=block_candidate,
        gtr=bound_gtr.consumer_metadata(),
        on_chain_anchor=on_chain_anchor.to_dict(),
    )


def record_to_api_response(
    record: MintQueueRecord,
    *,
    store: MintQueueStore | None = None,
) -> dict[str, Any]:
    """Map mint queue row to TP-101 GET /records response (7-year retention store)."""
    tp101 = record.block_candidate.get("tp101_record") or {}
    ledger_ref = record.submit_ref if record.status == "submitted" else None
    gtr_id = record.gtr_id or record.block_candidate.get("gtr_id")
    auditrail = None
    greenledger_entry = None
    if store is not None and gtr_id:
        auditrail = store.fetch_auditrail_by_gtr_id(str(gtr_id))
        greenledger_entry = store.fetch_greenledger_by_gtr_id(str(gtr_id))
    por_scores = record.block_candidate.get("tp102_rfm")
    return {
        "gtr_id": gtr_id,
        "record": tp101,
        "attestations": tp101.get("attestations", []),
        "on_chain_anchor": record.block_candidate.get("on_chain_anchor"),
        "auditrail": auditrail,
        "greenledger_entry": greenledger_entry,
        "por_scores": por_scores,
        "ledger_ref": ledger_ref,
        "status": record.status,
        "queue_id": record.id,
        "created_at": record.created_at,
        "submitted_at": record.submitted_at,
        "accepted_at": record.block_candidate.get("accepted_at"),
    }
