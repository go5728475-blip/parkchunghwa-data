"""Domain layer exports."""

from core.domain.aggregate import AggregateRoot
from core.domain.entity import Entity
from core.domain.events import (
    AnalysisSessionCreated,
    DomainErrorOccurred,
    DomainEvent,
    ExplanationTraceAdded,
    ReportCreated,
    ReportSectionAdded,
)
from core.domain.ids import (
    AggregateId,
    EntityId,
    EventId,
    PluginId,
    ProviderId,
    ReportId,
    SessionId,
    UserId,
)
from core.domain.report import Report, ReportStatus
from core.domain.session import AnalysisSession, SessionStatus
from core.domain.value_objects import (
    BirthData,
    ConfidenceScore,
    EngineContext,
    ExplanationTrace,
    ReportSection,
)

__all__ = [
    "AggregateId",
    "AggregateRoot",
    "AnalysisSession",
    "AnalysisSessionCreated",
    "BirthData",
    "ConfidenceScore",
    "DomainErrorOccurred",
    "DomainEvent",
    "EngineContext",
    "Entity",
    "EntityId",
    "EventId",
    "ExplanationTrace",
    "ExplanationTraceAdded",
    "PluginId",
    "ProviderId",
    "Report",
    "ReportCreated",
    "ReportId",
    "ReportSection",
    "ReportSectionAdded",
    "ReportStatus",
    "SessionId",
    "SessionStatus",
    "UserId",
]
