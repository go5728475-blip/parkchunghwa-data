"""Domain events."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from core.interfaces.event import IEvent


@dataclass(frozen=True, kw_only=True)
class DomainEvent:
    """Base immutable domain event compatible with IEvent."""

    event_id: UUID = field(default_factory=uuid4)
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    aggregate_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    version: int = 1
    event_type: str = ""
    payload: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.event_type:
            object.__setattr__(self, "event_type", self.__class__.__name__)
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
        if self.payload is None:
            object.__setattr__(self, "payload", {})


@dataclass(frozen=True, kw_only=True)
class AnalysisSessionCreated(DomainEvent):
    """Raised when a new analysis session is created."""


@dataclass(frozen=True, kw_only=True)
class ReportCreated(DomainEvent):
    """Raised when a new report aggregate is created."""


@dataclass(frozen=True, kw_only=True)
class ReportSectionAdded(DomainEvent):
    """Raised when a section is appended to a report."""


@dataclass(frozen=True, kw_only=True)
class ExplanationTraceAdded(DomainEvent):
    """Raised when an explanation trace is attached to a report."""


@dataclass(frozen=True, kw_only=True)
class DomainErrorOccurred(DomainEvent):
    """Raised when a domain-level error is recorded."""


IEvent.register(DomainEvent)
