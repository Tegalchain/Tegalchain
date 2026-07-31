"""Run: python -m tegalchain.greenledger integrity-check|export-cold"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from green_ledger_spec.integrity import IntegritySchedule

from tegalchain.queue.store import MintQueueStore
from tegalchain.submitter import DEFAULT_DB

from .export import export_cold_tier_entries
from .integrity_runner import run_and_persist_integrity_checks


def _store() -> MintQueueStore:
    db_path = Path(os.environ.get("TEGALCHAIN_MINT_QUEUE_DB", str(DEFAULT_DB)))
    return MintQueueStore(db_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="TP-103 GreenLedger ops (Phase 7)")
    parser.add_argument(
        "command",
        choices=["integrity-check", "export-cold"],
        help="run scheduled integrity checks or export cold-tier GLE rows",
    )
    parser.add_argument(
        "--schedule",
        choices=[s.value for s in IntegritySchedule],
        default=IntegritySchedule.DAILY.value,
        help="integrity schedule (integrity-check only)",
    )
    parser.add_argument(
        "--output-dir",
        default="tegalchain/data/cold_export",
        help="directory for JSONL cold export (export-cold only)",
    )
    args = parser.parse_args()
    store = _store()

    if args.command == "integrity-check":
        schedule = IntegritySchedule(args.schedule)
        result = run_and_persist_integrity_checks(store, schedule=schedule)
        print(json.dumps(result.to_dict(), indent=2))
        if result.violation_count:
            sys.exit(2)
        return

    export_dir = Path(args.output_dir)
    if not export_dir.is_absolute():
        export_dir = Path.cwd() / export_dir
    result = export_cold_tier_entries(store, export_dir)
    print(json.dumps(result.to_dict(), indent=2))


if __name__ == "__main__":
    main()
