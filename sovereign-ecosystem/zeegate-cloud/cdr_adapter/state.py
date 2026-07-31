"""Dedupe state for processed CDR call UUIDs."""

from __future__ import annotations

import sqlite3
from pathlib import Path


class CdrWatcherState:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_cdr (
                    cdr_uuid TEXT PRIMARY KEY,
                    gtr_id TEXT,
                    processed_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def is_processed(self, cdr_uuid: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM processed_cdr WHERE cdr_uuid = ?",
                (cdr_uuid,),
            ).fetchone()
        return row is not None

    def mark_processed(self, cdr_uuid: str, *, gtr_id: str | None = None) -> None:
        from datetime import UTC, datetime

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO processed_cdr (cdr_uuid, gtr_id, processed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(cdr_uuid) DO NOTHING
                """,
                (cdr_uuid, gtr_id, datetime.now(tz=UTC).isoformat()),
            )
            conn.commit()
