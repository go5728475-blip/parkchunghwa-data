"""SQLite-backed snapshot store."""

from __future__ import annotations

import sqlite3

from core.events.persistence.schema import ensure_schema
from core.events.persistence.serialization import record_to_snapshot, snapshot_to_record
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.models import Snapshot


class SQLiteSnapshotStore(ISnapshotStore):
    """Persistent snapshot store backed by SQLite."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._owns_connection = True
        self._autocommit = True
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        ensure_schema(self._connection)

    def bind_transaction(self, connection: sqlite3.Connection) -> None:
        """Use a shared connection and defer commits until transaction commit."""
        self._connection = connection
        self._owns_connection = False
        self._autocommit = False
        self._connection.row_factory = sqlite3.Row
        ensure_schema(self._connection)

    def _maybe_commit(self) -> None:
        if self._autocommit:
            self._connection.commit()

    @property
    def db_path(self) -> str:
        return self._db_path

    def close(self) -> None:
        if self._owns_connection:
            self._connection.close()

    def save(self, snapshot: Snapshot) -> None:
        record = snapshot_to_record(snapshot)
        self._connection.execute(
            """
            INSERT INTO snapshots (
                snapshot_id,
                aggregate_id,
                aggregate_type,
                aggregate_version,
                created_at,
                state_json
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                record["snapshot_id"],
                record["aggregate_id"],
                record["aggregate_type"],
                record["aggregate_version"],
                record["created_at"],
                record["state_json"],
            ),
        )
        self._maybe_commit()

    def get_latest(self, aggregate_id: str) -> Snapshot | None:
        cursor = self._connection.execute(
            """
            SELECT
                snapshot_id,
                aggregate_id,
                aggregate_type,
                aggregate_version,
                created_at,
                state_json
            FROM snapshots
            WHERE aggregate_id = ?
            ORDER BY aggregate_version DESC, sequence DESC
            LIMIT 1
            """,
            (aggregate_id,),
        )
        row = cursor.fetchone()
        if row is None:
            return None
        return record_to_snapshot(row)

    def list(self) -> tuple[Snapshot, ...]:
        cursor = self._connection.execute(
            """
            SELECT
                snapshot_id,
                aggregate_id,
                aggregate_type,
                aggregate_version,
                created_at,
                state_json
            FROM snapshots
            ORDER BY sequence ASC
            """,
        )
        return tuple(record_to_snapshot(row) for row in cursor.fetchall())

    def clear(self) -> None:
        self._connection.execute("DELETE FROM snapshots")
        self._maybe_commit()
