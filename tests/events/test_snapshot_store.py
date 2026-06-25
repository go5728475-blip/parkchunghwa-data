"""Tests for in-memory snapshot store."""

from __future__ import annotations

from core.events.snapshot.in_memory_store import InMemorySnapshotStore
from core.events.snapshot.models import Snapshot


def _snapshot(aggregate_id: str, version: int) -> Snapshot:
    return Snapshot(
        aggregate_id=aggregate_id,
        aggregate_type="workflow",
        aggregate_version=version,
        state={"event_count": version},
    )


def test_save_and_get_latest() -> None:
    store = InMemorySnapshotStore()
    first = _snapshot("wf-1", 10)
    second = _snapshot("wf-1", 20)
    store.save(first)
    store.save(second)

    assert store.get_latest("wf-1") == second


def test_list_returns_saved_snapshots() -> None:
    store = InMemorySnapshotStore()
    snapshots = (_snapshot("wf-1", 1), _snapshot("wf-2", 2))
    for snapshot in snapshots:
        store.save(snapshot)

    assert store.list() == snapshots


def test_get_latest_returns_none_when_missing() -> None:
    store = InMemorySnapshotStore()
    assert store.get_latest("missing") is None


def test_clear_removes_snapshots() -> None:
    store = InMemorySnapshotStore()
    store.save(_snapshot("wf-1", 1))

    store.clear()

    assert store.list() == ()
    assert store.get_latest("wf-1") is None
