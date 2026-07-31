"""Run TP-103 scheduled integrity checks against archived GLE rows."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from green_ledger_spec.integrity import IntegritySchedule, run_integrity_checks

from tegalchain.queue.store import MintQueueStore


@dataclass(frozen=True, slots=True)
class IntegrityRunResult:
    schedule: str
    checked_count: int
    violation_count: int
    violations: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schedule": self.schedule,
            "checked_count": self.checked_count,
            "violation_count": self.violation_count,
            "violations": self.violations,
        }


def run_and_persist_integrity_checks(
    store: MintQueueStore,
    *,
    schedule: IntegritySchedule = IntegritySchedule.DAILY,
    on_chain_refs: dict[str, str] | None = None,
) -> IntegrityRunResult:
    """Execute integrity checks and persist violations (never silent fix)."""
    gles = store.list_all_greenledger_entries()
    violations = run_integrity_checks(
        gles,
        schedule=schedule,
        on_chain_refs=on_chain_refs,
    )
    persisted: list[dict[str, Any]] = []
    for violation in violations:
        payload = violation.to_dict()
        store.save_integrity_violation(
            {
                **payload,
                "detected_at": payload["detected_at"],
                "payload": payload,
            }
        )
        persisted.append(payload)
    return IntegrityRunResult(
        schedule=schedule.value,
        checked_count=len(gles),
        violation_count=len(persisted),
        violations=persisted,
    )
