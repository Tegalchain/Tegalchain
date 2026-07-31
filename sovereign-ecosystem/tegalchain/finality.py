"""Deterministic transaction finality.

Once a transaction is in a committed block it is irreversible — no forks,
probabilistic finality, or confirmation depth. See docs/TEGALCHAIN.md#finality.
"""

from __future__ import annotations

from dataclasses import dataclass


class FinalityError(RuntimeError):
    """Raised when an operation assumes a finalized transaction that is not yet final."""


FINALIZED_QUEUE_STATUS = "submitted"


@dataclass(frozen=True, slots=True)
class FinalityProof:
    """Evidence that a transaction reached deterministic finality on the ledger."""

    telemetry_hash: str
    submit_ref: str
    submitted_at: str
    queue_id: int

    @property
    def irreversible(self) -> bool:
        return True


def is_finalized_status(status: str) -> bool:
    return status == FINALIZED_QUEUE_STATUS


def finality_proof_from_queue_record(record: object) -> FinalityProof:
    """Build a finality proof from a mint queue row after chain commit."""
    status = getattr(record, "status", None)
    if not is_finalized_status(str(status)):
        raise FinalityError(
            f"transaction queue_id={getattr(record, 'id', '?')} is not finalized "
            f"(status={status!r})"
        )

    submit_ref = getattr(record, "submit_ref", None)
    submitted_at = getattr(record, "submitted_at", None)
    if not submit_ref or not submitted_at:
        raise FinalityError("finalized record missing submit_ref or submitted_at")

    return FinalityProof(
        telemetry_hash=str(getattr(record, "telemetry_hash")),
        submit_ref=str(submit_ref),
        submitted_at=str(submitted_at),
        queue_id=int(getattr(record, "id")),
    )


def assert_no_reorg(expected_submit_ref: str, observed_submit_ref: str) -> None:
    """Permissioned ledgers must not rewrite committed submit references."""
    if expected_submit_ref != observed_submit_ref:
        raise FinalityError(
            "committed submit reference changed — violates deterministic finality"
        )
