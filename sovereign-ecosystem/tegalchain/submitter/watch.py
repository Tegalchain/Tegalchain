"""Periodic drain + anchor SLA monitoring for operational Phase 1 closure."""

from __future__ import annotations

import json
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tegalchain.queue.store import MintQueueStore
from tegalchain.submitter.drain import DrainResult, SubmitterConfig, drain_queue
from tegalchain.submitter.sla import AnchorSlaReport, build_anchor_sla_report


@dataclass(frozen=True, slots=True)
class WatchCycleResult:
    drain: DrainResult
    sla: AnchorSlaReport
    integrity_violation_count: int = 0


def run_watch_cycle(
    store: MintQueueStore,
    config: SubmitterConfig,
    *,
    limit: int = 20,
) -> WatchCycleResult:
    sla = build_anchor_sla_report(store.fetch_unanchored())
    drain = drain_queue(store, config, limit=limit)
    return WatchCycleResult(drain=drain, sla=sla)


def append_watch_log(log_file: Path, payload: dict[str, Any]) -> None:
    """Append one compact JSON line per watch cycle."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, separators=(",", ":")) + "\n")


def emit_sla_violations(report: AnchorSlaReport) -> None:
    for violation in report.violations:
        print(
            f"ANCHOR_SLA_VIOLATION queue_id={violation.queue_id} "
            f"gtr_id={violation.gtr_id!r} status={violation.status} "
            f"age_seconds={violation.age_seconds:.1f} sla_seconds={violation.sla_seconds}",
            file=sys.stderr,
        )


def watch_drain(
    store: MintQueueStore,
    config: SubmitterConfig,
    *,
    limit: int = 20,
    interval_seconds: int = 30,
    max_cycles: int | None = None,
    emit_json: bool = False,
    run_integrity: bool = False,
    log_file: Path | None = None,
) -> list[WatchCycleResult]:
    """Drain pending mints on an interval and report anchor SLA violations."""
    cycles: list[WatchCycleResult] = []
    iteration = 0
    while max_cycles is None or iteration < max_cycles:
        cycle = run_watch_cycle(store, config, limit=limit)
        cycles.append(cycle)
        emit_sla_violations(cycle.sla)
        integrity_violations = 0
        integrity: dict[str, Any] | None = None
        if run_integrity:
            from green_ledger_spec.integrity import IntegritySchedule
            from tegalchain.greenledger.integrity_runner import (
                run_and_persist_integrity_checks,
            )

            result = run_and_persist_integrity_checks(
                store,
                schedule=IntegritySchedule.DAILY,
            )
            integrity = result.to_dict()
            integrity_violations = result.violation_count
            if result.violation_count:
                print(
                    f"INTEGRITY_VIOLATION count={result.violation_count}",
                    file=sys.stderr,
                )
        payload: dict[str, Any] = {
            "cycle": iteration + 1,
            "drain": {
                "processed": cycle.drain.processed,
                "submitted": cycle.drain.submitted,
                "outboxed": cycle.drain.outboxed,
                "failed": cycle.drain.failed,
            },
            "sla": cycle.sla.to_dict(),
        }
        if integrity is not None:
            payload["integrity"] = integrity
        payload["logged_at"] = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        if log_file is not None:
            append_watch_log(log_file, payload)
        cycles[-1] = WatchCycleResult(
            drain=cycle.drain,
            sla=cycle.sla,
            integrity_violation_count=integrity_violations,
        )
        if emit_json:
            print(json.dumps(payload, indent=2))
        elif cycle.drain.processed or cycle.sla.violation_count or integrity_violations:
            print(json.dumps(payload))

        if cycle.drain.failed:
            return cycles

        iteration += 1
        if max_cycles is not None and iteration >= max_cycles:
            break
        time.sleep(interval_seconds)
    return cycles
