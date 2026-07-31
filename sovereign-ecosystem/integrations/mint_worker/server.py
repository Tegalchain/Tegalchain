"""Mint worker HTTP service — TP-101 gretelemetry oracle (HTTPS REST ingestion).

Transport: HTTPS REST (TLS 1.3+ in production). MQTT v5 topic patterns: mqtt_topics.py.
See docs/standards/TP-101-GREENTELEMETRY.md#ingestion-interface.
"""

from __future__ import annotations

import os
import sys
import uuid
from contextlib import asynccontextmanager
from functools import lru_cache
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from greentelemetry_protocol_spec.gtr import ReportingMode  # noqa: E402
from tegalchain.queue.store import MintQueueStore  # noqa: E402
from tegalchain.submitter import DEFAULT_DB  # noqa: E402
from tegalchain.submitter.sla import build_anchor_sla_report  # noqa: E402
from tegalchain.tegalid_gate import get_identity_mode  # noqa: E402
from tegalchain.zk_evidence import get_zk_mode  # noqa: E402

from . import __version__
from .auth import bearer_required, require_bearer  # noqa: E402
from .ingest import IngestError, ingest_payload, record_to_api_response  # noqa: E402
from .tp108_append import Tp108AppendError, append_attestation  # noqa: E402
from .mqtt_bridge import active_transports, maybe_start_mqtt_bridge  # noqa: E402

PROTOCOL_VERSION = (ROOT / "greentelemetry-protocol-spec" / "VERSION").read_text().strip()
MAX_BATCH_RECORDS = 1000


@asynccontextmanager
async def _lifespan(_app: FastAPI):
    mqtt_bridge = maybe_start_mqtt_bridge(_queue_store())
    yield
    if mqtt_bridge is not None:
        mqtt_bridge.stop()


app = FastAPI(
    title="Gretelemetry Oracle",
    description=(
        "TP-101 ingestion edge: HTTPS REST + optional MQTT v5 (gtp/{source_id}/…). "
        "Validate gretelemetry → tegalid gate → mint queue."
    ),
    version=__version__,
    lifespan=_lifespan,
)


class HealthResponse(BaseModel):
    status: str
    mint_worker_version: str
    protocol_version: str
    identity_mode: str
    zk_mode: str
    transports: list[str]
    features: list[str] = Field(
        default_factory=lambda: [
            "por_scores",
            "carbon_accounts",
            "bearer_ops_routes",
            "tp108_attestation_append",
        ],
        description="Optional API fields and route protections enabled by this build",
    )
    bearer_required: bool = False


class MintResponse(BaseModel):
    protocol_version: str
    mint_worker_version: str
    queue_id: int
    telemetry: dict[str, Any]
    identity: dict[str, Any]
    state_update: dict[str, Any]
    block_candidate: dict[str, Any]
    gtr: dict[str, Any]


class GtrCreatedResponse(BaseModel):
    gtr_id: str
    ledger_ref: str | None
    queue_id: int
    status: str


class BatchSubmitRequest(BaseModel):
    records: list[dict[str, Any]] = Field(..., min_length=1)


class BatchAcceptedResponse(BaseModel):
    batch_id: str
    status: str
    total: int
    accepted: int
    failed: int
    record_ids: list[int]
    errors: list[dict[str, Any]]


class QueueStatsResponse(BaseModel):
    pending: int
    outboxed: int
    submitted: int
    failed: int
    total: int


class AnchorSlaResponse(BaseModel):
    sla_seconds: int
    checked_at: str
    pending_count: int
    violation_count: int
    violations: list[dict[str, Any]]


@lru_cache(maxsize=1)
def _queue_store() -> MintQueueStore:
    db_path = Path(os.environ.get("TEGALCHAIN_MINT_QUEUE_DB", str(DEFAULT_DB)))
    return MintQueueStore(db_path)


def _reporting_mode_from_header(raw: str | None) -> ReportingMode:
    if raw is None or not raw.strip():
        return ReportingMode.STREAM
    try:
        return ReportingMode(raw.strip().lower())
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail="X-Gretelemetry-Reporting-Mode must be stream or batch",
        ) from exc


def _run_ingest(payload: dict[str, Any], request: Request):
    try:
        return ingest_payload(
            _queue_store(),
            payload,
            reporting_mode=_reporting_mode_from_header(
                request.headers.get("X-Gretelemetry-Reporting-Mode")
            ),
        )
    except IngestError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        mint_worker_version=__version__,
        protocol_version=PROTOCOL_VERSION,
        identity_mode=get_identity_mode().value,
        zk_mode=get_zk_mode().value,
        transports=active_transports(),
        bearer_required=bearer_required(),
    )


@app.post("/v1/telemetry/records", response_model=GtrCreatedResponse, status_code=201)
def submit_gtr_record(
    payload: dict[str, Any],
    request: Request,
    _: None = Depends(require_bearer),
) -> GtrCreatedResponse:
    """TP-101: submit a single canonical GTR (or legacy envelope normalized at oracle)."""
    result = _run_ingest(payload, request)
    return GtrCreatedResponse(
        gtr_id=result.gtr_id,
        ledger_ref=result.ledger_ref,
        queue_id=result.queue_id,
        status=result.status,
    )


@app.post("/v1/telemetry/batch", response_model=BatchAcceptedResponse, status_code=202)
def submit_gtr_batch(
    body: BatchSubmitRequest,
    request: Request,
    _: None = Depends(require_bearer),
) -> BatchAcceptedResponse:
    """TP-101: batch GTR submission (max 1,000 records)."""
    if len(body.records) > MAX_BATCH_RECORDS:
        raise HTTPException(
            status_code=413,
            detail=f"Batch exceeds maximum of {MAX_BATCH_RECORDS} records",
        )

    batch_id = str(uuid.uuid4())
    store = _queue_store()
    store.create_batch(batch_id=batch_id, total=len(body.records))

    record_ids: list[int] = []
    errors: list[dict[str, Any]] = []
    for index, record in enumerate(body.records):
        try:
            ingested = ingest_payload(
                store,
                record,
                reporting_mode=ReportingMode.BATCH,
            )
            record_ids.append(ingested.queue_id)
        except IngestError as exc:
            errors.append({"index": index, "detail": str(exc), "status_code": exc.status_code})

    accepted = len(record_ids)
    failed = len(errors)
    status = "completed" if failed == 0 else "completed_with_errors"
    store.finalize_batch(
        batch_id,
        status=status,
        accepted=accepted,
        failed=failed,
        record_ids=record_ids,
        errors=errors,
    )
    return BatchAcceptedResponse(
        batch_id=batch_id,
        status=status,
        total=len(body.records),
        accepted=accepted,
        failed=failed,
        record_ids=record_ids,
        errors=errors,
    )


@app.get("/v1/telemetry/batch/{batch_id}", response_model=BatchAcceptedResponse)
def get_batch_status(
    batch_id: str,
    _: None = Depends(require_bearer),
) -> BatchAcceptedResponse:
    batch = _queue_store().fetch_batch(batch_id)
    if batch is None:
        raise HTTPException(status_code=404, detail="batch_id not found")
    return BatchAcceptedResponse(
        batch_id=batch.batch_id,
        status=batch.status,
        total=batch.total,
        accepted=batch.accepted,
        failed=batch.failed,
        record_ids=batch.record_ids,
        errors=batch.errors or [],
    )


@app.get("/v1/telemetry/records/{gtr_id}")
def get_gtr_record(
    gtr_id: str,
    _: None = Depends(require_bearer),
) -> dict[str, Any]:
    """TP-101: return stored GTR, attestations, and ledger_ref."""
    record = _queue_store().fetch_by_gtr_id(gtr_id)
    if record is None:
        raise HTTPException(status_code=404, detail="gtr_id not found")
    return record_to_api_response(record, store=_queue_store())


@app.post("/v1/telemetry/records/{gtr_id}/attestations", status_code=200)
def append_gtr_attestation(
    gtr_id: str,
    attestation: dict[str, Any],
    _: None = Depends(require_bearer),
) -> dict[str, Any]:
    """TP-108: append a signed THIRD_PARTY attestation to an archived GTR."""
    try:
        record = append_attestation(_queue_store(), gtr_id, attestation)
    except Tp108AppendError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return record_to_api_response(record, store=_queue_store())


@app.post("/v1/telemetry", response_model=MintResponse)
def ingest_telemetry_legacy(
    payload: dict[str, Any],
    request: Request,
    _: None = Depends(require_bearer),
) -> MintResponse:
    """Legacy Phase 1 ingress (full mint worker response). Prefer POST /v1/telemetry/records."""
    result = _run_ingest(payload, request)
    return MintResponse(
        protocol_version=PROTOCOL_VERSION,
        mint_worker_version=__version__,
        queue_id=result.queue_id,
        telemetry=result.telemetry,
        identity=result.identity,
        state_update=result.state_update,
        block_candidate=result.block_candidate,
        gtr=result.gtr,
    )


@app.get("/v1/queue/stats", response_model=QueueStatsResponse)
def queue_stats(_: None = Depends(require_bearer)) -> QueueStatsResponse:
    stats = _queue_store().stats()
    return QueueStatsResponse(**stats)


@app.get("/v1/queue/anchor-sla", response_model=AnchorSlaResponse)
def anchor_sla_status(_: None = Depends(require_bearer)) -> AnchorSlaResponse:
    report = build_anchor_sla_report(_queue_store().fetch_unanchored())
    payload = report.to_dict()
    return AnchorSlaResponse(
        sla_seconds=int(payload["sla_seconds"]),
        checked_at=str(payload["checked_at"]),
        pending_count=int(payload["pending_count"]),
        violation_count=int(payload["violation_count"]),
        violations=list(payload["violations"]),  # type: ignore[arg-type]
    )


@app.get("/v1/greenledger/carbon-accounts/{source_id}")
def get_carbon_account(
    source_id: str,
    period_start: str | None = None,
    period_end: str | None = None,
    _: None = Depends(require_bearer),
) -> dict[str, Any]:
    """TP-103: materialised Carbon Account for a source entity."""
    store = _queue_store()
    if period_start and period_end:
        account = store.fetch_carbon_account(source_id, period_start, period_end)
    elif period_start or period_end:
        raise HTTPException(
            status_code=400,
            detail="Provide both period_start and period_end, or neither for latest",
        )
    else:
        account = store.fetch_latest_carbon_account(source_id)
    if account is None:
        raise HTTPException(status_code=404, detail="carbon account not found")
    return account
