"""Drain mint queue to Tegalchain — ordering phase of the transaction lifecycle.

Submits queued transaction proposals to the chain node (ordering → validation/commit).
See docs/TEGALCHAIN.md#transaction-flow and tegalchain-core/docs/transaction-flow.md.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tegalchain.auditrail import correlate_submitted_record
from tegalchain.queue.store import MintQueueRecord, MintQueueStore
from tegalchain.anchor import (
    GtrOnChainAnchor,
    build_merkle_batch_anchors,
    finalize_anchor_for_submit,
)
from tegalchain.endorsement import assert_ready_for_ordering
from tegalchain.finality import finality_proof_from_queue_record
from tegalchain.gossip import GossipFanout, publish_submitted_transaction

from .backends import SubmitterBackend, backend_submits_to_chain
from .config import (
    DEFAULT_DB,
    DEFAULT_OUTBOX,
    SubmitterConfig,
)
from .submit import submit_block_candidate


@dataclass(frozen=True, slots=True)
class DrainResult:
    processed: int
    submitted: int
    outboxed: int
    failed: int


def write_outbox_record(
    outbox_dir: Path,
    record: MintQueueRecord,
    *,
    block_candidate: dict[str, Any] | None = None,
) -> Path:
    outbox_dir.mkdir(parents=True, exist_ok=True)
    path = outbox_dir / f"{record.id:06d}_{record.telemetry_hash[:16]}.json"
    candidate = block_candidate if block_candidate is not None else record.block_candidate
    payload = {
        "queue_id": record.id,
        "telemetry_hash": record.telemetry_hash,
        "block_candidate": candidate,
        "state_update": record.state_update,
        "identity": record.identity,
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def _prepare_block_candidate_for_submit(block_candidate: dict[str, Any]) -> dict[str, Any]:
    """Finalize on-chain anchor timestamp before ordering."""
    prepared = dict(block_candidate)
    raw_anchor = prepared.get("on_chain_anchor")
    if isinstance(raw_anchor, dict) and raw_anchor.get("type") == "GTR_ANCHOR":
        anchor = finalize_anchor_for_submit(
            GtrOnChainAnchor(
                gtr_id=str(raw_anchor["gtr_id"]),
                content_hash=str(raw_anchor["content_hash"]),
                attester_ids=tuple(raw_anchor.get("attester_ids", [])),
                measurement_type=str(raw_anchor["measurement_type"]),
                timestamp=str(raw_anchor["timestamp"]),
                anchor_timestamp=raw_anchor.get("anchor_timestamp"),
            )
        )
        prepared["on_chain_anchor"] = anchor.to_dict()
    return prepared


def drain_queue(
    store: MintQueueStore,
    config: SubmitterConfig,
    *,
    limit: int = 20,
    gossip_fanout: GossipFanout | None = None,
) -> DrainResult:
    records = store.fetch_pending(limit=limit)
    submitted = outboxed = failed = 0
    use_merkle_batch = os.environ.get("TEGALCHAIN_MERKLE_BATCH", "").lower() in {
        "1",
        "true",
        "yes",
    }
    merkle_batch: dict[str, Any] | None = None
    if use_merkle_batch and len(records) > 1:
        anchors: list[GtrOnChainAnchor] = []
        for record in records:
            raw = record.block_candidate.get("on_chain_anchor") or {}
            if raw.get("type") != "GTR_ANCHOR":
                continue
            anchors.append(
                GtrOnChainAnchor(
                    gtr_id=str(raw["gtr_id"]),
                    content_hash=str(raw["content_hash"]),
                    attester_ids=tuple(raw.get("attester_ids", [])),
                    measurement_type=str(raw["measurement_type"]),
                    timestamp=str(raw["timestamp"]),
                    anchor_timestamp=raw.get("anchor_timestamp"),
                )
            )
        if len(anchors) > 1:
            merkle_batch = build_merkle_batch_anchors(anchors).to_dict()

    submits_to_chain = backend_submits_to_chain(config.backend)

    for record in records:
        try:
            assert_ready_for_ordering(record.block_candidate)
            candidate = _prepare_block_candidate_for_submit(record.block_candidate)
            if merkle_batch is not None:
                candidate["merkle_batch"] = merkle_batch
                proof = merkle_batch.get("proofs", {}).get(
                    candidate.get("on_chain_anchor", {}).get("gtr_id", "")
                )
                if proof is not None:
                    candidate["merkle_proof"] = proof
            outbox_path = write_outbox_record(
                config.outbox_dir, record, block_candidate=candidate
            )
            if submits_to_chain:
                submit_ref = submit_block_candidate(
                    candidate,
                    config,
                    queue_id=record.id,
                )
                candidate = dict(candidate)
                candidate["submit_backend"] = config.backend.value
                store.mark_submitted(
                    record.id,
                    submit_ref,
                    block_candidate=candidate,
                )
                committed = store.fetch_by_id(record.id)
                if committed is not None:
                    finality_proof_from_queue_record(committed)
                    correlate_submitted_record(
                        store,
                        committed,
                        block_candidate=candidate,
                    )
                submitted += 1
                if gossip_fanout is not None:
                    publish_submitted_transaction(
                        gossip_fanout,
                        channel_id="greenledger",
                        signer_peer="submitter.peer",
                        block_number=record.id,
                        block_candidate=record.block_candidate,
                        submit_ref=submit_ref,
                    )
            else:
                store.mark_outboxed(
                    record.id,
                    str(outbox_path),
                    block_candidate=candidate,
                )
                outboxed += 1
        except Exception as exc:  # noqa: BLE001 — record per-item failure
            store.mark_failed(record.id, str(exc))
            failed += 1

    return DrainResult(
        processed=len(records),
        submitted=submitted,
        outboxed=outboxed,
        failed=failed,
    )
