"""SQLite transaction unit of work."""

from __future__ import annotations

import sqlite3

from core.events.interfaces import IEventBus
from core.events.snapshot.sqlite_store import SQLiteSnapshotStore
from core.events.store.sqlite_store import SQLiteEventStore
from core.metrics.interfaces import IMetricsCollector
from core.metrics.recording import MetricsRecorder
from core.uow.context import TransactionContext
from core.uow.interfaces import IUnitOfWork
from core.uow.support import (
    TransactionEventPublisher,
    mark_committed,
    mark_rolled_back,
    mark_started,
)
from core.uow.metrics_support import TransactionMetricsSupport


class SQLiteUnitOfWork(IUnitOfWork):
    """SQLite-backed transaction boundary using BEGIN/COMMIT/ROLLBACK."""

    def __init__(
        self,
        db_path: str,
        event_store: SQLiteEventStore,
        snapshot_store: SQLiteSnapshotStore,
        event_bus: IEventBus | None = None,
        aggregate_id: str = "workflow-transaction",
        metrics_collector: IMetricsCollector | None = None,
    ) -> None:
        self._db_path = db_path
        self._connection = sqlite3.connect(db_path)
        self._connection.row_factory = sqlite3.Row
        self._event_store = event_store
        self._snapshot_store = snapshot_store
        self._event_bus = event_bus
        self._aggregate_id = aggregate_id
        self._context = TransactionContext()
        self._publisher = TransactionEventPublisher(event_bus, aggregate_id)
        self._transaction_metrics = TransactionMetricsSupport(
            MetricsRecorder(metrics_collector),
        )
        self._event_store.bind_transaction(self._connection)
        self._snapshot_store.bind_transaction(self._connection)

    @property
    def context(self) -> TransactionContext:
        return self._context

    @property
    def transaction_trace(self) -> tuple:
        return tuple(self._publisher.trace_entries)

    @property
    def db_path(self) -> str:
        return self._db_path

    def begin(self) -> None:
        if self._context.active:
            msg = "Transaction is already active."
            raise RuntimeError(msg)
        self._connection.execute("BEGIN")
        mark_started(self._context)
        self._transaction_metrics.on_begin()
        self._publisher.publish_started()

    def commit(self) -> None:
        if not self._context.active:
            msg = "No active transaction to commit."
            raise RuntimeError(msg)
        self._publisher.publish_committed()
        self._connection.commit()
        self._transaction_metrics.on_commit()
        mark_committed(self._context)

    def rollback(self) -> None:
        if not self._context.active:
            return
        self._publisher.publish_rolled_back("workflow rollback")
        self._connection.rollback()
        self._transaction_metrics.on_rollback()
        mark_rolled_back(self._context)

    def close(self) -> None:
        self._connection.close()
