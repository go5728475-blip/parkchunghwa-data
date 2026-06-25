"""SQLite schema for published events and snapshots."""

from __future__ import annotations

import sqlite3

EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS events (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id TEXT NOT NULL UNIQUE,
    event_type TEXT NOT NULL,
    aggregate_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    payload_json TEXT NOT NULL
)
"""

SNAPSHOTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS snapshots (
    sequence INTEGER PRIMARY KEY AUTOINCREMENT,
    snapshot_id TEXT NOT NULL UNIQUE,
    aggregate_id TEXT NOT NULL,
    aggregate_type TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    state_json TEXT NOT NULL
)
"""


def ensure_schema(connection: sqlite3.Connection) -> None:
    """Create persistence tables when they do not exist."""
    connection.execute(EVENTS_TABLE_SQL)
    connection.execute(SNAPSHOTS_TABLE_SQL)
    connection.commit()


def tables_exist(connection: sqlite3.Connection) -> bool:
    """Return True when both persistence tables exist."""
    cursor = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('events', 'snapshots')",
    )
    names = {row[0] for row in cursor.fetchall()}
    return names == {"events", "snapshots"}
