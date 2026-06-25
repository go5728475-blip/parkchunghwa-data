"""Application queries."""

from __future__ import annotations

from dataclasses import dataclass

from core.contracts.metadata import Metadata
from core.contracts.query import Query
from core.domain.ids import ReportId, SessionId


@dataclass(frozen=True, kw_only=True)
class GetAnalysisSession(Query):
    """Fetch a single analysis session."""

    session_id: SessionId


@dataclass(frozen=True, kw_only=True)
class GetReport(Query):
    """Fetch a single report."""

    report_id: ReportId


@dataclass(frozen=True, kw_only=True)
class ListReports(Query):
    """List reports, optionally filtered by session."""

    session_id: SessionId | None = None


@dataclass(frozen=True, kw_only=True)
class GetEventsByAggregate(Query):
    """Load events for an aggregate."""

    aggregate_id: str


@dataclass(frozen=True, kw_only=True)
class GetEventsByType(Query):
    """Load events by event type."""

    event_type: str


@dataclass(frozen=True, kw_only=True)
class ListCapabilities(Query):
    """List analysis capabilities from registered plugins."""


@dataclass(frozen=True, kw_only=True)
class ListProviders(Query):
    """List registered provider metadata from the provider catalog."""
