"""Refresh materialised Carbon Accounts after GLE archival."""

from __future__ import annotations

from calendar import monthrange
from datetime import UTC, datetime

from green_ledger_spec.carbon_account import aggregate_carbon_account
from green_ledger_spec.models import GreenLedgerEntry
from green_ledger_spec.validate import validate_carbon_account_payload

from tegalchain.queue.store import MintQueueStore


def _month_period(reference_timestamp: str) -> tuple[str, str]:
    dt = datetime.fromisoformat(reference_timestamp.replace("Z", "+00:00"))
    start = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day = monthrange(start.year, start.month)[1]
    end = start.replace(day=last_day, hour=23, minute=59, second=59)
    return (
        start.strftime("%Y-%m-%dT%H:%M:%SZ"),
        end.strftime("%Y-%m-%dT%H:%M:%SZ"),
    )


def refresh_carbon_account_for_gle(
    store: MintQueueStore,
    gle: GreenLedgerEntry | dict,
    *,
    expected_gtr_count: int = 1,
) -> dict:
    """Recompute and persist the Carbon Account for the GLE's source + month."""
    payload = gle.to_dict() if isinstance(gle, GreenLedgerEntry) else gle
    source_id = str(payload["source_id"])
    period_start, period_end = _month_period(str(payload["measurement_timestamp"]))
    gles = store.query_greenledger(source_id=source_id, limit=10_000)
    account = aggregate_carbon_account(
        source_id=source_id,
        period_start=period_start,
        period_end=period_end,
        gles=gles,
        expected_gtr_count=expected_gtr_count,
    )
    body = account.to_dict()
    validate_carbon_account_payload(body)
    store.save_carbon_account(body)
    return body
