"""In-memory transaction unit of work."""

from __future__ import annotations

from core.events.interfaces import IEventBus
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.store.interfaces import IEventStore
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
from core.uow.transactional_stores import TransactionalEventStore, TransactionalSnapshotStore
from core.uow.metrics_support import TransactionMetricsSupport


class InMemoryUnitOfWork(IUnitOfWork):
    """Logical transaction boundary for in-memory stores."""

    def __init__(
        self,
        event_store: IEventStore,
        snapshot_store: ISnapshotStore,
        event_bus: IEventBus | None = None,
        aggregate_id: str = "workflow-transaction",
        metrics_collector: IMetricsCollector | None = None,
    ) -> None:
        self._event_store = self._as_transactional_event_store(event_store)
        self._snapshot_store = self._as_transactional_snapshot_store(snapshot_store)
        self._event_bus = event_bus
        self._aggregate_id = aggregate_id
        self._context = TransactionContext()
        self._publisher = TransactionEventPublisher(event_bus, aggregate_id)
        self._transaction_metrics = TransactionMetricsSupport(
            MetricsRecorder(metrics_collector),
        )

    @property
    def context(self) -> TransactionContext:
        return self._context

    @property
    def transaction_trace(self) -> tuple:
        return tuple(self._publisher.trace_entries)

    def begin(self) -> None:
        if self._context.active:
            msg = "Transaction is already active."
            raise RuntimeError(msg)
        self._event_store.begin_buffering()
        self._snapshot_store.begin_buffering()
        mark_started(self._context)
        self._transaction_metrics.on_begin()
        self._publisher.publish_started()

    def commit(self) -> None:
        if not self._context.active:
            msg = "No active transaction to commit."
            raise RuntimeError(msg)
        self._event_store.commit_buffer()
        self._snapshot_store.commit_buffer()
        self._publisher.publish_committed()
        self._transaction_metrics.on_commit()
        mark_committed(self._context)

    def rollback(self) -> None:
        if not self._context.active:
            return
        self._publisher.publish_rolled_back("workflow rollback")
        self._event_store.rollback_buffer()
        self._snapshot_store.rollback_buffer()
        self._transaction_metrics.on_rollback()
        mark_rolled_back(self._context)

    @staticmethod
    def _as_transactional_event_store(store: IEventStore) -> TransactionalEventStore:
        if isinstance(store, TransactionalEventStore):
            return store
        return TransactionalEventStore(store)

    @staticmethod
    def _as_transactional_snapshot_store(store: ISnapshotStore) -> TransactionalSnapshotStore:
        if isinstance(store, TransactionalSnapshotStore):
            return store
        return TransactionalSnapshotStore(store)
