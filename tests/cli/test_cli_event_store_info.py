"""Tests for event-store-info CLI command."""

from __future__ import annotations

from pathlib import Path

from core.bootstrap.configuration import EngineConfiguration
from core.cli.main import event_store_info
from core.events.event_types import AnalysisStarted
from core.events.store.sqlite_store import SQLiteEventStore


def test_cli_event_store_info_inmemory(capsys) -> None:
    exit_code = event_store_info(EngineConfiguration(event_storage="inmemory"))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Event Store Info" in captured.out
    assert "Storage Type:   inmemory" in captured.out
    assert "Database Path:  -" in captured.out


def test_cli_event_store_info_sqlite(capsys, tmp_path: Path) -> None:
    db_path = str(tmp_path / "master_engine.db")
    store = SQLiteEventStore(db_path)
    store.append(AnalysisStarted(aggregate_id="session-1"))
    store.close()

    config = EngineConfiguration(event_storage="sqlite", sqlite_path=db_path)
    exit_code = event_store_info(config)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Storage Type:   sqlite" in captured.out
    assert "Event Count:    1" in captured.out
    assert db_path in captured.out


def test_factory_switches_between_storage_backends(tmp_path: Path) -> None:
    from core.bootstrap.factory import ApplicationFactory

    factory = ApplicationFactory(EngineConfiguration(event_storage="inmemory"))
    assert factory.create_event_store().__class__.__name__ == "InMemoryEventStore"

    db_path = str(tmp_path / "switch.db")
    sqlite_factory = ApplicationFactory(
        EngineConfiguration(event_storage="sqlite", sqlite_path=db_path),
    )
    assert sqlite_factory.create_event_store().__class__.__name__ == "SQLiteEventStore"
    assert sqlite_factory.create_snapshot_store().__class__.__name__ == "SQLiteSnapshotStore"
