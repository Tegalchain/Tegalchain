"""TP-103 GreenLedger bridge — archive GLE on chain submit."""

from __future__ import annotations

from typing import Any

from green_ledger_spec.gle import build_greenledger_entry
from green_ledger_spec.models import GreenLedgerEntry, RetentionClass
from green_ledger_spec.validate import validate_gle_payload

from tegalchain.queue.store import MintQueueRecord, MintQueueStore


def archive_submitted_gtr(
    store: MintQueueStore,
    record: MintQueueRecord,
    *,
    block_candidate: dict[str, Any],
    retention_class: RetentionClass = RetentionClass.STANDARD,
    tags: tuple[str, ...] = (),
) -> GreenLedgerEntry:
    """Build and persist a GLE after successful on-chain submit."""
    if not record.submit_ref:
        raise ValueError("submitted queue record required for GreenLedger archival")
    gle = build_greenledger_entry(
        block_candidate=block_candidate,
        ledger_ref=str(record.submit_ref),
        submitted_at=record.submitted_at,
        retention_class=retention_class,
        tags=tags,
    )
    payload = gle.to_dict()
    validate_gle_payload(payload)
    store.save_greenledger_entry(payload)
    from tegalchain.greenledger.carbon import refresh_carbon_account_for_gle

    refresh_carbon_account_for_gle(store, payload)
    return gle
