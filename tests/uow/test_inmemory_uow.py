"""Tests for in-memory transaction unit of work."""

from __future__ import annotations

import pytest

from core.events.event_types import AnalysisStarted, TransactionCommitted, TransactionStarted
from core.events.in_memory_bus import InMemoryEventBus
from core.events.snapshot.in_memory_store import InMemorySnapshotStore
from core.events.store.in_memory_store import InMemoryEventStore
from core.uow.in_memory import InMemoryUnitOfWork


def _uow() -> InMemoryUnitOfWork:
    bus = InMemoryEventBus()
    store = InMemoryEventStore()
    snapshots = InMemorySnapshotStore()
    return InMemoryUnitOfWork(store, snapshots, bus)


def test_inmemory_uow_begin_commit() -> None:
    uow = _uow()

    uow.begin()
    uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))
    uow.commit()

    assert uow.context.committed is True
    assert uow.context.active is False
    assert len(uow._event_store.delegate.list()) == 1


def test_inmemory_uow_rollback_discards_buffered_events() -> None:
    uow = _uow()

    uow.begin()
    uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))
    uow.rollback()

    assert uow.context.rolled_back is True
    assert len(uow._event_store.delegate.list()) == 0


def test_inmemory_uow_context_manager_commits() -> None:
    uow = _uow()

    with uow:
        uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))

    assert uow.context.committed is True
    assert len(uow._event_store.delegate.list()) == 1


def test_inmemory_uow_context_manager_rolls_back_on_exception() -> None:
    uow = _uow()

    with pytest.raises(RuntimeError, match="boom"):
        with uow:
            uow._event_store.append(AnalysisStarted(aggregate_id="session-1"))
            raise RuntimeError("boom")

    assert uow.context.rolled_back is True
    assert len(uow._event_store.delegate.list()) == 0


def test_inmemory_uow_publishes_transaction_events_and_trace() -> None:
    bus = InMemoryEventBus()
    uow = InMemoryUnitOfWork(InMemoryEventStore(), InMemorySnapshotStore(), bus)

    with uow:
        pass

    event_types = [event.event_type for event in bus.recent_events()]
    assert TransactionStarted.__name__ in event_types
    assert TransactionCommitted.__name__ in event_types
    assert any(entry.source == "transaction" for entry in uow.transaction_trace)


def test_inmemory_uow_commit_without_begin_raises() -> None:
    uow = _uow()

    with pytest.raises(RuntimeError, match="No active transaction"):
        uow.commit()


def test_inmemory_uow_begin_twice_raises() -> None:
    uow = _uow()
    uow.begin()

    with pytest.raises(RuntimeError, match="already active"):
        uow.begin()
