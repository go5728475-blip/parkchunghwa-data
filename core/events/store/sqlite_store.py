"""SQLite-backed published event store."""

from __future__ import annotations

import sqlite3

from core.events.models import DomainEvent
from core.events.persistence.schema import ensure_schema
from core.events.persistence.serialization import event_to_record, record_to_event
from core.events.store.interfaces import EventNotFoundError, IEventStore


class SQLiteEventStore(IEventStore):
    """Persistent event store backed by SQLite."""

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

    def append(self, event: DomainEvent) -> None:
        record = event_to_record(event)
        self._connection.execute(
            """
            INSERT INTO events (
                event_id, event_type, aggregate_id, occurred_at, payload_json
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                record["event_id"],
                record["event_type"],
                record["aggregate_id"],
                record["occurred_at"],
                record["payload_json"],
            ),
        )
        self._maybe_commit()

    def append_many(self, events: tuple[DomainEvent, ...] | list[DomainEvent]) -> None:
        for event in events:
            self.append(event)

    def get(self, event_id: str) -> DomainEvent:
        cursor = self._connection.execute(
            """
            SELECT event_id, event_type, aggregate_id, occurred_at, payload_json
            FROM events
            WHERE event_id = ?
            """,
            (event_id,),
        )
        row = cursor.fetchone()
        if row is None:
            msg = f"Event not found: {event_id}"
            raise EventNotFoundError(msg)
        return record_to_event(row)

    def list(self) -> tuple[DomainEvent, ...]:
        cursor = self._connection.execute(
            """
            SELECT event_id, event_type, aggregate_id, occurred_at, payload_json
            FROM events
            ORDER BY sequence ASC
            """,
        )
        return tuple(record_to_event(row) for row in cursor.fetchall())

    def list_by_aggregate(self, aggregate_id: str) -> tuple[DomainEvent, ...]:
        cursor = self._connection.execute(
            """
            SELECT event_id, event_type, aggregate_id, occurred_at, payload_json
            FROM events
            WHERE aggregate_id = ?
            ORDER BY sequence ASC
            """,
            (aggregate_id,),
        )
        return tuple(record_to_event(row) for row in cursor.fetchall())

    def clear(self) -> None:
        self._connection.execute("DELETE FROM events")
        self._maybe_commit()
