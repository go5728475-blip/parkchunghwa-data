"""Tests for domain events."""

from __future__ import annotations

from uuid import uuid4

from core.domain.events import AnalysisSessionCreated, DomainEvent
from core.interfaces.event import IEvent


def test_domain_event_uses_class_name_as_default_event_type() -> None:
    event = AnalysisSessionCreated(aggregate_id="agg-1")
    assert event.event_type == "AnalysisSessionCreated"


def test_domain_event_is_ievent_compatible() -> None:
    event = DomainEvent(aggregate_id="agg-1", version=2, payload={"key": "value"})
    assert isinstance(event, IEvent)
    assert event.aggregate_id == "agg-1"
    assert event.version == 2
    assert event.payload["key"] == "value"
    assert event.event_id is not None


def test_domain_event_accepts_explicit_event_id() -> None:
    event_id = uuid4()
    event = DomainEvent(event_id=event_id, aggregate_id="agg-2")
    assert event.event_id == event_id
