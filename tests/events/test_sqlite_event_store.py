"""Tests for SQLite event store."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from core.events.event_types import AnalysisCompleted, AnalysisStarted
from core.events.persistence.schema import tables_exist
from core.events.store.interfaces import EventNotFoundError
from core.events.store.sqlite_store import SQLiteEventStore


@pytest.fixture
def db_path(tmp_path: Path) -> str:
    return str(tmp_path / "events.db")


def test_append_and_get(db_path: str) -> None:
    store = SQLiteEventStore(db_path)
    event = AnalysisStarted(aggregate_id="session-1", payload={"capability": "stub.analysis"})
    store.append(event)

    loaded = store.get(event.event_id)
    assert loaded == event
    store.close()


def test_restart_loads_persisted_events(db_path: str) -> None:
    event = AnalysisCompleted(aggregate_id="session-1", payload={"status": "ok"})
    store = SQLiteEventStore(db_path)
    store.append(event)
    store.close()

    reloaded = SQLiteEventStore(db_path)
    assert reloaded.list() == (event,)
    reloaded.close()


def test_list_by_aggregate(db_path: str) -> None:
    store = SQLiteEventStore(db_path)
    first = AnalysisStarted(aggregate_id="session-1")
    second = AnalysisCompleted(aggregate_id="session-2")
    store.append_many((first, second))

    assert store.list_by_aggregate("session-1") == (first,)
    store.close()


def test_clear_removes_events(db_path: str) -> None:
    store = SQLiteEventStore(db_path)
    event = AnalysisStarted(aggregate_id="session-1")
    store.append(event)
    store.clear()

    assert store.list() == ()
    with pytest.raises(EventNotFoundError):
        store.get(event.event_id)
    store.close()


def test_schema_is_created_automatically(db_path: str) -> None:
    store = SQLiteEventStore(db_path)
    connection = sqlite3.connect(db_path)
    assert tables_exist(connection)
    connection.close()
    store.close()
