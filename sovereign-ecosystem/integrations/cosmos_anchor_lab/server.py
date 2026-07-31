"""Lab Cosmos REST anchor — mimics future x/auditrail gretelemetry handler."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Tegalchain Cosmos Anchor Lab",
    version="0.1.0",
    description="Phase 5 lab stub for TEGALCHAIN_SUBMITTER_BACKEND=cosmos",
)


class AnchorRequest(BaseModel):
    type: str = Field(..., description="TELEMETRY_MINT")
    block_candidate: dict[str, Any]
    on_chain_anchor: dict[str, Any] = Field(default_factory=dict)


class AnchorResponse(BaseModel):
    txhash: str
    height: int | None = None
    gtr_id: str | None = None


def _lab_txhash(block_candidate: dict[str, Any], *, queue_hint: str = "") -> str:
    """Deterministic 64-char hex ref (not LABMOCK-) for lab verification."""
    canonical = json.dumps(block_candidate, separators=(",", ":"), sort_keys=True)
    if queue_hint:
        canonical = f"{canonical}|{queue_hint}"
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest().upper()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "cosmos-anchor-lab"}


@app.post("/tegalchain/gretelemetry/v1/anchor", response_model=AnchorResponse)
def anchor_telemetry(body: AnchorRequest) -> AnchorResponse:
    if body.type != "TELEMETRY_MINT":
        raise HTTPException(status_code=400, detail=f"unsupported type: {body.type}")

    candidate = body.block_candidate
    anchor = body.on_chain_anchor or candidate.get("on_chain_anchor") or {}
    if anchor.get("type") != "GTR_ANCHOR":
        raise HTTPException(status_code=400, detail="on_chain_anchor.type must be GTR_ANCHOR")

    gtr_id = str(anchor.get("gtr_id", ""))
    txhash = _lab_txhash(candidate, queue_hint=gtr_id)
    return AnchorResponse(txhash=txhash, height=1, gtr_id=gtr_id or None)
