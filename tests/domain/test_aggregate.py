"""Tests for aggregate root base class."""

from __future__ import annotations

from core.domain.aggregate import AggregateRoot
from core.domain.events import DomainEvent
from core.domain.ids import AggregateId


def test_aggregate_records_and_pulls_events() -> None:
    aggregate = AggregateRoot(id=AggregateId.new())
    event = DomainEvent(aggregate_id=str(aggregate.id))
    aggregate.record_event(event)
    pulled = aggregate.pull_events()
    assert pulled == [event]
    assert aggregate.domain_events == []


def test_aggregate_clear_events() -> None:
    aggregate = AggregateRoot(id=AggregateId.new())
    aggregate.record_event(DomainEvent(aggregate_id=str(aggregate.id)))
    aggregate.clear_events()
    assert aggregate.domain_events == []
    assert aggregate.pull_events() == []
