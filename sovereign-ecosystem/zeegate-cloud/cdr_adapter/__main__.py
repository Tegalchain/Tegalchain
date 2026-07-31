"""CLI: watch FreeSWITCH CDR CSV and publish to mint worker."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parent
REPO_ROOT = PKG_ROOT.parents[1]
ZEEGATE_CLOUD = PKG_ROOT.parent
for path in (str(REPO_ROOT), str(ZEEGATE_CLOUD)):
    if path not in sys.path:
        sys.path.insert(0, path)

from cdr_adapter.adapter import CdrAdapter, CdrAdapterConfig  # noqa: E402
from cdr_adapter.state import CdrWatcherState  # noqa: E402
from cdr_adapter.watcher import process_cdr_directory, watch_cdr_directory  # noqa: E402


def _default_bindings() -> Path:
    return REPO_ROOT / "tegalchain" / "data" / "tegalid_bindings.example.json"


def _default_cdr_dir() -> Path:
    return Path(os.environ.get("ZEEGATE_CDR_DIR", "/var/log/freeswitch/cdr-csv"))


def _default_state_db() -> Path:
    return Path(
        os.environ.get(
            "ZEEGATE_CDR_STATE_DB",
            str(REPO_ROOT / "tegalchain" / "data" / "cdr_watcher.db"),
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Zeegate CDR adapter — normalize CSV CDR to GTR and POST to mint worker"
    )
    parser.add_argument(
        "command",
        choices=["once", "watch"],
        help="process CDR directory once or on an interval",
    )
    parser.add_argument("--cdr-dir", type=Path, default=_default_cdr_dir())
    parser.add_argument("--state-db", type=Path, default=_default_state_db())
    parser.add_argument("--bindings", type=Path, default=_default_bindings())
    parser.add_argument(
        "--mint-worker-url",
        default=os.environ.get("MINT_WORKER_URL"),
        help="POST GTRs here (omit to build-only)",
    )
    parser.add_argument(
        "--bearer-token",
        default=os.environ.get("MINT_WORKER_BEARER_TOKEN"),
    )
    parser.add_argument("--interval", type=int, default=15)
    parser.add_argument("--cycles", type=int, default=None)
    args = parser.parse_args()

    adapter = CdrAdapter(
        CdrAdapterConfig(
            bindings_file=args.bindings if args.bindings.is_file() else None,
            fallback_source_id=os.environ.get("ZEEGATE_CDR_FALLBACK_SOURCE", "edge001"),
            mint_worker_url=args.mint_worker_url,
            bearer_token=args.bearer_token,
        )
    )
    state = CdrWatcherState(args.state_db)

    if args.command == "once":
        result = process_cdr_directory(adapter, args.cdr_dir, state)
        print(
            json.dumps(
                {
                    "scanned_files": result.scanned_files,
                    "processed_rows": result.processed_rows,
                    "skipped_rows": result.skipped_rows,
                    "errors": list(result.errors),
                    "responses": list(result.responses),
                },
                indent=2,
            )
        )
        if result.errors:
            sys.exit(1)
        return

    cycles = watch_cdr_directory(
        adapter,
        args.cdr_dir,
        state,
        interval_seconds=args.interval,
        max_cycles=args.cycles,
    )
    print(
        json.dumps(
            [
                {
                    "cycle": index + 1,
                    "processed_rows": cycle.processed_rows,
                    "skipped_rows": cycle.skipped_rows,
                    "errors": list(cycle.errors),
                }
                for index, cycle in enumerate(cycles)
            ],
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
