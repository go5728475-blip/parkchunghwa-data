"""Tests for SQLite snapshot store."""

from __future__ import annotations

from pathlib import Path

from core.events.snapshot.models import Snapshot
from core.events.snapshot.sqlite_store import SQLiteSnapshotStore


def test_save_and_get_latest(tmp_path: Path) -> None:
    db_path = str(tmp_path / "snapshots.db")
    store = SQLiteSnapshotStore(db_path)
    first = Snapshot(
        aggregate_id="wf-1",
        aggregate_type="workflow",
        aggregate_version=10,
        state={"event_count": 10},
    )
    second = Snapshot(
        aggregate_id="wf-1",
        aggregate_type="workflow",
        aggregate_version=20,
        state={"event_count": 20},
    )
    store.save(first)
    store.save(second)

    assert store.get_latest("wf-1") == second
    store.close()


def test_restart_loads_persisted_snapshots(tmp_path: Path) -> None:
    db_path = str(tmp_path / "snapshots.db")
    snapshot = Snapshot(
        aggregate_id="wf-1",
        aggregate_type="workflow",
        aggregate_version=5,
        state={"event_count": 5},
    )
    store = SQLiteSnapshotStore(db_path)
    store.save(snapshot)
    store.close()

    reloaded = SQLiteSnapshotStore(db_path)
    assert reloaded.list() == (snapshot,)
    assert reloaded.get_latest("wf-1") == snapshot
    reloaded.close()


def test_clear_removes_snapshots(tmp_path: Path) -> None:
    db_path = str(tmp_path / "snapshots.db")
    store = SQLiteSnapshotStore(db_path)
    store.save(
        Snapshot(
            aggregate_id="wf-1",
            aggregate_type="workflow",
            aggregate_version=1,
            state={"event_count": 1},
        ),
    )
    store.clear()

    assert store.list() == ()
    assert store.get_latest("wf-1") is None
    store.close()
