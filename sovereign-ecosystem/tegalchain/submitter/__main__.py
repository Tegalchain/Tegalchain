"""Run: python -m tegalchain.submitter drain|stats|sla-check|watch"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tegalchain.queue.store import MintQueueStore
from tegalchain.submitter import SubmitterConfig, drain_queue
from tegalchain.submitter.sla import build_anchor_sla_report
from tegalchain.submitter.watch import watch_drain


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Tegalchain mint queue submitter (Phase 1c)"
    )
    parser.add_argument(
        "command",
        choices=["drain", "stats", "sla-check", "watch"],
        help="drain pending mints, show stats, check anchor SLA, or watch+drain loop",
    )
    parser.add_argument("--limit", type=int, default=20, help="max records per drain")
    parser.add_argument(
        "--interval",
        type=int,
        default=30,
        help="seconds between watch cycles (watch command only)",
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=None,
        help="max watch cycles (default: run until failure or interrupt)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit structured JSON on watch cycles",
    )
    parser.add_argument(
        "--integrity",
        action="store_true",
        help="run TP-103 daily integrity check each watch cycle (Phase 7)",
    )
    parser.add_argument(
        "--log",
        metavar="FILE",
        default=None,
        help="append one JSON line per watch cycle to FILE (Phase 7 soak)",
    )
    args = parser.parse_args()

    config = SubmitterConfig.from_env()
    store = MintQueueStore(config.db_path)

    if args.command == "stats":
        print(json.dumps(store.stats(), indent=2))
        return

    if args.command == "sla-check":
        report = build_anchor_sla_report(store.fetch_unanchored())
        print(json.dumps(report.to_dict(), indent=2))
        if report.violation_count:
            sys.exit(2)
        return

    if args.command == "watch":
        cycles = watch_drain(
            store,
            config,
            limit=args.limit,
            interval_seconds=args.interval,
            max_cycles=args.cycles,
            emit_json=args.json,
            run_integrity=args.integrity,
            log_file=Path(args.log) if args.log else None,
        )
        if cycles and cycles[-1].drain.failed:
            sys.exit(1)
        if cycles and cycles[-1].sla.violation_count:
            sys.exit(2)
        if cycles and cycles[-1].integrity_violation_count:
            sys.exit(2)
        return

    result = drain_queue(store, config, limit=args.limit)
    sla = build_anchor_sla_report(store.fetch_unanchored())
    print(
        json.dumps(
            {
                "processed": result.processed,
                "submitted": result.submitted,
                "outboxed": result.outboxed,
                "failed": result.failed,
                "backend": config.backend.value,
                "db": str(config.db_path),
                "outbox": str(config.outbox_dir),
                "api_url": config.api_url,
                "cosmos_rest_url": config.cosmos_rest_url,
                "has_privkey": bool(config.privkey),
                "anchor_sla": sla.to_dict(),
            },
            indent=2,
        )
    )

    if result.failed:
        sys.exit(1)
    if sla.violation_count:
        sys.exit(2)


if __name__ == "__main__":
    main()
