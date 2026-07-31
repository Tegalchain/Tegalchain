"""TP-101 anchor SLA monitoring — pending GTRs must reach chain within 60s."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from greentelemetry_protocol_spec.security import ANCHOR_SLA_SECONDS

from tegalchain.queue.store import MintQueueRecord


@dataclass(frozen=True, slots=True)
class AnchorSlaViolation:
    queue_id: int
    gtr_id: str | None
    status: str
    accepted_at: str
    age_seconds: float
    sla_seconds: int


@dataclass(frozen=True, slots=True)
class AnchorSlaReport:
    sla_seconds: int
    checked_at: str
    pending_count: int
    violation_count: int
    violations: tuple[AnchorSlaViolation, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "sla_seconds": self.sla_seconds,
            "checked_at": self.checked_at,
            "pending_count": self.pending_count,
            "violation_count": self.violation_count,
            "violations": [
                {
                    "queue_id": item.queue_id,
                    "gtr_id": item.gtr_id,
                    "status": item.status,
                    "accepted_at": item.accepted_at,
                    "age_seconds": round(item.age_seconds, 3),
                    "sla_seconds": item.sla_seconds,
                }
                for item in self.violations
            ],
        }


def _parse_timestamp(value: str) -> datetime:
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).astimezone(UTC)


def acceptance_time(record: MintQueueRecord) -> datetime:
    """When the oracle accepted the GTR (fallback: queue row created_at)."""
    raw = record.block_candidate.get("accepted_at")
    if isinstance(raw, str) and raw.strip():
        return _parse_timestamp(raw)
    return _parse_timestamp(record.created_at)


def anchor_sla_violation(
    record: MintQueueRecord,
    *,
    now: datetime | None = None,
    sla_seconds: int = ANCHOR_SLA_SECONDS,
) -> AnchorSlaViolation | None:
    if record.status not in {"pending", "outboxed"}:
        return None
    accepted = acceptance_time(record)
    current = now or datetime.now(tz=UTC)
    age = (current - accepted).total_seconds()
    if age <= sla_seconds:
        return None
    return AnchorSlaViolation(
        queue_id=record.id,
        gtr_id=record.gtr_id,
        status=record.status,
        accepted_at=accepted.isoformat(),
        age_seconds=age,
        sla_seconds=sla_seconds,
    )


def build_anchor_sla_report(
    records: list[MintQueueRecord],
    *,
    sla_seconds: int = ANCHOR_SLA_SECONDS,
    now: datetime | None = None,
) -> AnchorSlaReport:
    current = now or datetime.now(tz=UTC)
    unanchored = [record for record in records if record.status in {"pending", "outboxed"}]
    violations = [
        violation
        for record in unanchored
        if (violation := anchor_sla_violation(record, now=current, sla_seconds=sla_seconds))
        is not None
    ]
    return AnchorSlaReport(
        sla_seconds=sla_seconds,
        checked_at=current.isoformat(),
        pending_count=len(unanchored),
        violation_count=len(violations),
        violations=tuple(violations),
    )
