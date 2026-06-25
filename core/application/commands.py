"""Application commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from core.contracts.command import Command
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, ReportId, SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext, ExplanationTrace, ReportSection


@dataclass(frozen=True, kw_only=True)
class CreateAnalysisSession(Command):
    """Create a new analysis session."""

    user_id: UserId
    birth_data: BirthData


@dataclass(frozen=True, kw_only=True)
class StartAnalysisSession(Command):
    """Start an existing analysis session."""

    session_id: SessionId


@dataclass(frozen=True, kw_only=True)
class CompleteAnalysisSession(Command):
    """Mark an analysis session as completed."""

    session_id: SessionId


@dataclass(frozen=True, kw_only=True)
class FailAnalysisSession(Command):
    """Mark an analysis session as failed."""

    session_id: SessionId
    reason: str


@dataclass(frozen=True, kw_only=True)
class CreateReport(Command):
    """Create a report for a session."""

    session_id: SessionId


@dataclass(frozen=True, kw_only=True)
class AddReportSection(Command):
    """Append a section to a report."""

    report_id: ReportId
    section: ReportSection


@dataclass(frozen=True, kw_only=True)
class AddExplanationTrace(Command):
    """Attach an explanation trace to a report."""

    report_id: ReportId
    trace: ExplanationTrace


@dataclass(frozen=True, kw_only=True)
class CompleteReport(Command):
    """Complete a report."""

    report_id: ReportId


@dataclass(frozen=True, kw_only=True)
class RunAnalysis(Command):
    """Execute a full analysis run through the engine."""

    session_id: SessionId
    user_id: UserId
    birth_data: BirthData
    context: EngineContext
    capability: str = "stub.analysis"
    provider_id: ProviderId | None = None

    def __post_init__(self) -> None:
        if self.provider_id is not None and not str(self.provider_id).strip():
            msg = "Provider id cannot be blank."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class GenerateText(Command):
    """Generate text through a registered provider."""

    provider_id: ProviderId
    prompt: str
    context: dict[str, Any] | None = None

    def __post_init__(self) -> None:
        if not str(self.provider_id).strip():
            msg = "Provider id cannot be blank."
            raise ValueError(msg)
        if not self.prompt or not self.prompt.strip():
            msg = "Prompt cannot be empty."
            raise ValueError(msg)
