"""In-memory unit of work implementation."""

from __future__ import annotations

from core.domain.aggregate import AggregateRoot
from core.domain.report import Report
from core.domain.session import AnalysisSession
from core.infrastructure.memory_event_publisher import InMemoryEventPublisher
from core.infrastructure.memory_event_store import InMemoryEventStore
from core.infrastructure.memory_repository import (
    InMemoryAnalysisSessionRepository,
    InMemoryReportRepository,
)


class InMemoryUnitOfWork:
    """Coordinates in-memory repositories, event store, and publisher."""

    def __init__(self) -> None:
        self.sessions = InMemoryAnalysisSessionRepository()
        self.reports = InMemoryReportRepository()
        self.event_store = InMemoryEventStore()
        self.event_publisher = InMemoryEventPublisher()
        self._new_aggregates: list[AggregateRoot] = []
        self._dirty_aggregates: list[AggregateRoot] = []
        self._event_sources: list[AggregateRoot] = []

    def register_new(self, aggregate: AggregateRoot) -> None:
        """Track a newly created aggregate for persistence on commit."""
        self._new_aggregates.append(aggregate)
        self.collect_events(aggregate)

    def register_dirty(self, aggregate: AggregateRoot) -> None:
        """Track a modified aggregate for persistence on commit."""
        self._dirty_aggregates.append(aggregate)
        self.collect_events(aggregate)

    def collect_events(self, aggregate: AggregateRoot) -> None:
        """Track an aggregate whose pending events should flush on commit."""
        if aggregate not in self._event_sources:
            self._event_sources.append(aggregate)

    def commit(self) -> None:
        """Persist aggregates, append events to the store, and publish them."""
        for aggregate in self._new_aggregates:
            self._save_aggregate(aggregate)
        for aggregate in self._dirty_aggregates:
            self._save_aggregate(aggregate)

        events = []
        for aggregate in self._event_sources:
            events.extend(aggregate.pull_events())

        if events:
            self.event_store.append_many(events)
            self.event_publisher.publish_many(events)

        self._new_aggregates.clear()
        self._dirty_aggregates.clear()
        self._event_sources.clear()

    def rollback(self) -> None:
        """Discard pending domain events without storing or publishing."""
        for aggregate in self._event_sources:
            aggregate.clear_events()
        self._new_aggregates.clear()
        self._dirty_aggregates.clear()
        self._event_sources.clear()

    def _save_aggregate(self, aggregate: AggregateRoot) -> None:
        if isinstance(aggregate, AnalysisSession):
            self.sessions.save(aggregate)
        elif isinstance(aggregate, Report):
            self.reports.save(aggregate)
