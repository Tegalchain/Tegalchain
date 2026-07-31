"""SQLite-backed mint queue for Phase 1c Tegalchain submission.

This is an **application outbox** for ``TELEMETRY_MINT`` transaction proposals —
not the peer state database (LevelDB / CouchDB on chain nodes).
See tegalchain.state.StateLayer and docs/TEGALCHAIN.md#state-database.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class MintQueueRecord:
    id: int
    created_at: str
    telemetry_hash: str
    gtr_id: str | None
    block_candidate: dict[str, Any]
    state_update: dict[str, Any]
    identity: dict[str, Any]
    status: str
    submitted_at: str | None
    submit_ref: str | None
    error: str | None


@dataclass(frozen=True, slots=True)
class TelemetryBatchRecord:
    batch_id: str
    created_at: str
    status: str
    total: int
    accepted: int
    failed: int
    record_ids: list[int]
    errors: list[dict[str, Any]] | None


class MintQueueStore:
    """Persist TELEMETRY_MINT candidates until submitted to Tegalchain."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mint_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    telemetry_hash TEXT NOT NULL UNIQUE,
                    gtr_id TEXT,
                    block_candidate TEXT NOT NULL,
                    state_update TEXT NOT NULL,
                    identity TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    submitted_at TEXT,
                    submit_ref TEXT,
                    error TEXT
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mint_queue_status ON mint_queue(status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_mint_queue_gtr_id ON mint_queue(gtr_id)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS telemetry_batches (
                    batch_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    total INTEGER NOT NULL,
                    accepted INTEGER NOT NULL DEFAULT 0,
                    failed INTEGER NOT NULL DEFAULT 0,
                    record_ids TEXT NOT NULL DEFAULT '[]',
                    errors TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS source_rate_limits (
                    source_id TEXT NOT NULL,
                    hour_bucket TEXT NOT NULL,
                    record_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (source_id, hour_bucket)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS auditrail_correlations (
                    gtr_id TEXT PRIMARY KEY,
                    queue_id INTEGER NOT NULL,
                    telemetry_hash TEXT NOT NULL,
                    submit_ref TEXT NOT NULL,
                    submitted_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    auditrail_record_type TEXT NOT NULL,
                    anchor_timestamp TEXT,
                    tegalid_did TEXT,
                    project_id TEXT,
                    binding_id TEXT,
                    correlated_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_auditrail_submit_ref
                ON auditrail_correlations(submit_ref)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS greenledger_entries (
                    gle_id TEXT PRIMARY KEY,
                    gtr_id TEXT NOT NULL UNIQUE,
                    ledger_ref TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    measurement_type TEXT NOT NULL,
                    archive_timestamp TEXT NOT NULL,
                    retention_class TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_greenledger_gtr_id
                ON greenledger_entries(gtr_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_greenledger_source_id
                ON greenledger_entries(source_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_greenledger_ledger_ref
                ON greenledger_entries(ledger_ref)
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS carbon_accounts (
                    source_id TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    PRIMARY KEY (source_id, period_start, period_end)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS greenledger_integrity_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    gle_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    schedule TEXT NOT NULL,
                    detail TEXT NOT NULL,
                    detected_at TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            self._ensure_column(conn, "mint_queue", "gtr_id", "TEXT")
            conn.commit()

    @staticmethod
    def _ensure_column(
        conn: sqlite3.Connection, table: str, column: str, ddl_type: str
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        names = {str(row[1]) for row in rows}
        if column not in names:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl_type}")

    def enqueue(
        self,
        *,
        telemetry_hash: str,
        block_candidate: dict[str, Any],
        state_update: dict[str, Any],
        identity: dict[str, Any],
        gtr_id: str | None = None,
    ) -> int:
        with self._connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO mint_queue (
                    created_at, telemetry_hash, gtr_id, block_candidate,
                    state_update, identity, status
                ) VALUES (?, ?, ?, ?, ?, ?, 'pending')
                ON CONFLICT(telemetry_hash) DO UPDATE SET
                    created_at=excluded.created_at,
                    gtr_id=excluded.gtr_id,
                    block_candidate=excluded.block_candidate,
                    state_update=excluded.state_update,
                    identity=excluded.identity,
                    status='pending',
                    submitted_at=NULL,
                    submit_ref=NULL,
                    error=NULL
                """,
                (
                    _utc_now(),
                    telemetry_hash,
                    gtr_id,
                    json.dumps(block_candidate, separators=(",", ":"), sort_keys=True),
                    json.dumps(state_update, separators=(",", ":"), sort_keys=True),
                    json.dumps(identity, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()
            if cursor.lastrowid:
                return int(cursor.lastrowid)
            row = conn.execute(
                "SELECT id FROM mint_queue WHERE telemetry_hash = ?",
                (telemetry_hash,),
            ).fetchone()
            return int(row["id"])

    def fetch_pending(self, limit: int = 20) -> list[MintQueueRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM mint_queue
                WHERE status IN ('pending', 'outboxed')
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def fetch_by_id(self, record_id: int) -> MintQueueRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM mint_queue WHERE id = ?",
                (record_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def fetch_by_gtr_id(self, gtr_id: str) -> MintQueueRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM mint_queue WHERE gtr_id = ? ORDER BY id DESC LIMIT 1",
                (gtr_id,),
            ).fetchone()
        if row is None:
            return None
        return self._row_to_record(row)

    def fetch_recent(self, limit: int = 50) -> list[MintQueueRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM mint_queue ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def create_batch(
        self,
        *,
        batch_id: str,
        total: int,
        status: str = "processing",
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO telemetry_batches (
                    batch_id, created_at, status, total, accepted, failed, record_ids
                ) VALUES (?, ?, ?, ?, 0, 0, '[]')
                """,
                (batch_id, _utc_now(), status, total),
            )
            conn.commit()

    def finalize_batch(
        self,
        batch_id: str,
        *,
        status: str,
        accepted: int,
        failed: int,
        record_ids: list[int],
        errors: list[dict[str, Any]] | None = None,
    ) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE telemetry_batches
                SET status = ?, accepted = ?, failed = ?,
                    record_ids = ?, errors = ?
                WHERE batch_id = ?
                """,
                (
                    status,
                    accepted,
                    failed,
                    json.dumps(record_ids),
                    json.dumps(errors or []),
                    batch_id,
                ),
            )
            conn.commit()

    def fetch_batch(self, batch_id: str) -> TelemetryBatchRecord | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM telemetry_batches WHERE batch_id = ?",
                (batch_id,),
            ).fetchone()
        if row is None:
            return None
        return TelemetryBatchRecord(
            batch_id=str(row["batch_id"]),
            created_at=str(row["created_at"]),
            status=str(row["status"]),
            total=int(row["total"]),
            accepted=int(row["accepted"]),
            failed=int(row["failed"]),
            record_ids=json.loads(row["record_ids"]),
            errors=json.loads(row["errors"]) if row["errors"] else None,
        )

    def check_and_increment_source_rate(
        self,
        source_id: str,
        *,
        max_per_hour: int = 10_000,
    ) -> None:
        hour_bucket = datetime.now(timezone.utc).strftime("%Y%m%d%H")
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT record_count FROM source_rate_limits
                WHERE source_id = ? AND hour_bucket = ?
                """,
                (source_id, hour_bucket),
            ).fetchone()
            current = int(row["record_count"]) if row else 0
            if current >= max_per_hour:
                raise ValueError(
                    f"source_id {source_id!r} exceeded rate limit "
                    f"({max_per_hour} records per hour)"
                )
            conn.execute(
                """
                INSERT INTO source_rate_limits (source_id, hour_bucket, record_count)
                VALUES (?, ?, 1)
                ON CONFLICT(source_id, hour_bucket) DO UPDATE SET
                    record_count = record_count + 1
                """,
                (source_id, hour_bucket),
            )
            conn.commit()

    def fetch_unanchored(self, limit: int = 500) -> list[MintQueueRecord]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM mint_queue
                WHERE status IN ('pending', 'outboxed')
                ORDER BY id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def save_auditrail_correlation(self, correlation: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO auditrail_correlations (
                    gtr_id, queue_id, telemetry_hash, submit_ref, submitted_at,
                    content_hash, auditrail_record_type, anchor_timestamp,
                    tegalid_did, project_id, binding_id, correlated_at, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(gtr_id) DO UPDATE SET
                    queue_id=excluded.queue_id,
                    telemetry_hash=excluded.telemetry_hash,
                    submit_ref=excluded.submit_ref,
                    submitted_at=excluded.submitted_at,
                    content_hash=excluded.content_hash,
                    auditrail_record_type=excluded.auditrail_record_type,
                    anchor_timestamp=excluded.anchor_timestamp,
                    tegalid_did=excluded.tegalid_did,
                    project_id=excluded.project_id,
                    binding_id=excluded.binding_id,
                    correlated_at=excluded.correlated_at,
                    payload=excluded.payload
                """,
                (
                    str(correlation["gtr_id"]),
                    int(correlation["queue_id"]),
                    str(correlation["telemetry_hash"]),
                    str(correlation["submit_ref"]),
                    str(correlation["submitted_at"]),
                    str(correlation["content_hash"]),
                    str(correlation["auditrail_record_type"]),
                    correlation.get("anchor_timestamp"),
                    correlation.get("tegalid_did"),
                    correlation.get("project_id"),
                    correlation.get("binding_id"),
                    str(correlation["correlated_at"]),
                    json.dumps(correlation, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()

    def fetch_auditrail_by_gtr_id(self, gtr_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM auditrail_correlations WHERE gtr_id = ?",
                (gtr_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def save_greenledger_entry(self, entry: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO greenledger_entries (
                    gle_id, gtr_id, ledger_ref, source_id, measurement_type,
                    archive_timestamp, retention_class, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(gtr_id) DO UPDATE SET
                    gle_id=excluded.gle_id,
                    ledger_ref=excluded.ledger_ref,
                    source_id=excluded.source_id,
                    measurement_type=excluded.measurement_type,
                    archive_timestamp=excluded.archive_timestamp,
                    retention_class=excluded.retention_class,
                    payload=excluded.payload
                """,
                (
                    str(entry["gle_id"]),
                    str(entry["gtr_id"]),
                    str(entry["ledger_ref"]),
                    str(entry["source_id"]),
                    str(entry["measurement_type"]),
                    str(entry["archive_timestamp"]),
                    str(entry["retention_class"]),
                    json.dumps(entry, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()

    def fetch_greenledger_by_gtr_id(self, gtr_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM greenledger_entries WHERE gtr_id = ?",
                (gtr_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def fetch_greenledger_by_gle_id(self, gle_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT payload FROM greenledger_entries WHERE gle_id = ?",
                (gle_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def query_greenledger(
        self,
        *,
        source_id: str | None = None,
        measurement_type: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[Any] = []
        if source_id is not None:
            clauses.append("source_id = ?")
            params.append(source_id)
        if measurement_type is not None:
            clauses.append("measurement_type = ?")
            params.append(measurement_type)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(
                f"""
                SELECT payload FROM greenledger_entries
                {where}
                ORDER BY archive_timestamp DESC
                LIMIT ?
                """,
                tuple(params),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def list_all_greenledger_entries(self, *, limit: int = 10_000) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT payload FROM greenledger_entries
                ORDER BY archive_timestamp DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def save_carbon_account(self, account: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO carbon_accounts (source_id, period_start, period_end, payload)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(source_id, period_start, period_end) DO UPDATE SET
                    payload=excluded.payload
                """,
                (
                    str(account["source_id"]),
                    str(account["period_start"]),
                    str(account["period_end"]),
                    json.dumps(account, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()

    def fetch_carbon_account(
        self,
        source_id: str,
        period_start: str,
        period_end: str,
    ) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payload FROM carbon_accounts
                WHERE source_id = ? AND period_start = ? AND period_end = ?
                """,
                (source_id, period_start, period_end),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def fetch_latest_carbon_account(self, source_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT payload FROM carbon_accounts
                WHERE source_id = ?
                ORDER BY period_end DESC
                LIMIT 1
                """,
                (source_id,),
            ).fetchone()
        if row is None:
            return None
        return json.loads(row["payload"])

    def save_integrity_violation(self, violation: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO greenledger_integrity_violations (
                    gle_id, kind, schedule, detail, detected_at, payload
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(violation["gle_id"]),
                    str(violation["kind"]),
                    str(violation["schedule"]),
                    str(violation["detail"]),
                    str(violation["detected_at"]),
                    json.dumps(violation, separators=(",", ":"), sort_keys=True),
                ),
            )
            conn.commit()

    def mark_submitted(
        self,
        record_id: int,
        submit_ref: str,
        *,
        block_candidate: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as conn:
            if block_candidate is not None:
                conn.execute(
                    """
                    UPDATE mint_queue
                    SET status = 'submitted',
                        submitted_at = ?,
                        submit_ref = ?,
                        block_candidate = ?,
                        error = NULL
                    WHERE id = ?
                    """,
                    (
                        _utc_now(),
                        submit_ref,
                        json.dumps(block_candidate, separators=(",", ":"), sort_keys=True),
                        record_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE mint_queue
                    SET status = 'submitted',
                        submitted_at = ?,
                        submit_ref = ?,
                        error = NULL
                    WHERE id = ?
                    """,
                    (_utc_now(), submit_ref, record_id),
                )
            conn.commit()

    def mark_outboxed(
        self,
        record_id: int,
        outbox_path: str,
        *,
        block_candidate: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as conn:
            if block_candidate is not None:
                conn.execute(
                    """
                    UPDATE mint_queue
                    SET status = 'outboxed',
                        submit_ref = ?,
                        block_candidate = ?,
                        error = NULL
                    WHERE id = ?
                    """,
                    (
                        outbox_path,
                        json.dumps(block_candidate, separators=(",", ":"), sort_keys=True),
                        record_id,
                    ),
                )
            else:
                conn.execute(
                    """
                    UPDATE mint_queue
                    SET status = 'outboxed',
                        submit_ref = ?,
                        error = NULL
                    WHERE id = ?
                    """,
                    (outbox_path, record_id),
                )
            conn.commit()

    def update_block_candidate(
        self,
        record_id: int,
        block_candidate: dict[str, Any],
    ) -> MintQueueRecord:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE mint_queue
                SET block_candidate = ?
                WHERE id = ?
                """,
                (
                    json.dumps(block_candidate, separators=(",", ":"), sort_keys=True),
                    record_id,
                ),
            )
            conn.commit()
        updated = self.fetch_by_id(record_id)
        if updated is None:
            raise KeyError(f"mint queue record not found: {record_id}")
        return updated

    def mark_failed(self, record_id: int, error: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE mint_queue
                SET status = 'failed',
                    error = ?
                WHERE id = ?
                """,
                (error[:2000], record_id),
            )
            conn.commit()

    def stats(self) -> dict[str, int]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT status, COUNT(*) AS count FROM mint_queue GROUP BY status"
            ).fetchall()
        result = {"pending": 0, "outboxed": 0, "submitted": 0, "failed": 0}
        for row in rows:
            result[row["status"]] = int(row["count"])
        result["total"] = sum(result.values())
        return result

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MintQueueRecord:
        return MintQueueRecord(
            id=int(row["id"]),
            created_at=str(row["created_at"]),
            telemetry_hash=str(row["telemetry_hash"]),
            gtr_id=row["gtr_id"],
            block_candidate=json.loads(row["block_candidate"]),
            state_update=json.loads(row["state_update"]),
            identity=json.loads(row["identity"]),
            status=str(row["status"]),
            submitted_at=row["submitted_at"],
            submit_ref=row["submit_ref"],
            error=row["error"],
        )
