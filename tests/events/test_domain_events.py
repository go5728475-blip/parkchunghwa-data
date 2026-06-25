"""Tests for domain event models and types."""

from __future__ import annotations

from core.events.event_types import (
    AnalysisCompleted,
    AnalysisStarted,
    CapabilityExecuted,
    ProviderCalled,
    ProviderCompleted,
    ReportBuilt,
    ReportExported,
    WorkflowCompleted,
    WorkflowStarted,
)
from core.events.models import DomainEvent


def test_domain_event_sets_default_event_type() -> None:
    event = DomainEvent(aggregate_id="agg-1", payload={"key": "value"})

    assert event.event_type == "DomainEvent"
    assert event.event_id
    assert event.occurred_at
    assert event.payload == {"key": "value"}


def test_typed_events_inherit_domain_event() -> None:
    events = [
        WorkflowStarted(aggregate_id="wf-1"),
        WorkflowCompleted(aggregate_id="wf-1"),
        AnalysisStarted(aggregate_id="session-1"),
        AnalysisCompleted(aggregate_id="session-1"),
        CapabilityExecuted(aggregate_id="wealth.analysis"),
        ProviderCalled(aggregate_id="openai.stub"),
        ProviderCompleted(aggregate_id="openai.stub"),
        ReportBuilt(aggregate_id="report-1"),
        ReportExported(aggregate_id="report-1"),
    ]

    for event in events:
        assert isinstance(event, DomainEvent)
        assert event.event_type == event.__class__.__name__
