"""Tests for SQLite transaction unit of work."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.bootstrap.configuration import EngineConfiguration
from core.events.event_types import AnalysisStarted, TransactionCommitted, TransactionStarted
from core.events.in_memory_bus import InMemoryEventBus
from core.events.snapshot.sqlite_store import SQLiteSnapshotStore
from core.events.store.sqlite_store import SQLiteEventStore
from core.uow.sqlite import SQLiteUnitOfWork


def _sqlite_uow(tmp_path: Path) -> SQLiteUnitOfWork:
    db_path = str(tmp_path / "transaction.db")
    bus = InMemoryEventBus()
    event_store = SQLiteEventStore(db_path)
    snapshot_store = SQLiteSnapshotStore(db_path)
    return SQLiteUnitOfWork(db_path, event_store, snapshot_store, bus)


def test_sqlite_uow_begin_commit_persists_events(tmp_path: Path) -> None:
    uow = _sqlite_uow(tmp_path)

    uow.begin()
    uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))
    uow.commit()
    uow.close()

    verify_store = SQLiteEventStore(str(tmp_path / "transaction.db"))
    try:
        assert len(verify_store.list()) == 1
    finally:
        verify_store.close()


def test_sqlite_uow_rollback_discards_uncommitted_events(tmp_path: Path) -> None:
    uow = _sqlite_uow(tmp_path)

    uow.begin()
    uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))
    uow.rollback()
    uow.close()

    verify_store = SQLiteEventStore(str(tmp_path / "transaction.db"))
    try:
        assert len(verify_store.list()) == 0
    finally:
        verify_store.close()


def test_sqlite_uow_context_manager_commits(tmp_path: Path) -> None:
    uow = _sqlite_uow(tmp_path)

    with uow:
        uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))
    uow.close()

    verify_store = SQLiteEventStore(str(tmp_path / "transaction.db"))
    try:
        assert uow.context.committed is True
        assert len(verify_store.list()) == 1
    finally:
        verify_store.close()


def test_sqlite_uow_publishes_transaction_events(tmp_path: Path) -> None:
    bus = InMemoryEventBus()
    db_path = str(tmp_path / "transaction.db")
    uow = SQLiteUnitOfWork(
        db_path,
        SQLiteEventStore(db_path),
        SQLiteSnapshotStore(db_path),
        bus,
    )

    with uow:
        pass
    uow.close()

    event_types = [event.event_type for event in bus.recent_events()]
    assert TransactionStarted.__name__ in event_types
    assert TransactionCommitted.__name__ in event_types


def test_factory_creates_sqlite_unit_of_work(tmp_path: Path) -> None:
    from core.bootstrap.factory import ApplicationFactory

    db_path = str(tmp_path / "factory.db")
    factory = ApplicationFactory(
        EngineConfiguration(event_storage="sqlite", sqlite_path=db_path),
    )
    event_store = factory.create_event_store()
    snapshot_store = factory.create_snapshot_store()
    uow = factory.create_unit_of_work(event_store, snapshot_store)

    assert uow.__class__.__name__ == "SQLiteUnitOfWork"
    if hasattr(uow, "close"):
        uow.close()
    event_store.close()
    snapshot_store.close()


def test_sqlite_uow_commit_without_begin_raises(tmp_path: Path) -> None:
    uow = _sqlite_uow(tmp_path)

    with pytest.raises(RuntimeError, match="No active transaction"):
        uow.commit()

    uow.close()
