"""Report aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from core.domain.aggregate import AggregateRoot
from core.domain.events import (
    ExplanationTraceAdded,
    ReportCreated,
    ReportSectionAdded,
)
from core.domain.ids import AggregateId, ReportId, SessionId
from core.domain.value_objects import ExplanationTrace, ReportSection


class ReportStatus(StrEnum):
    """Lifecycle states for a report."""

    DRAFT = "DRAFT"
    COMPLETED = "COMPLETED"


@dataclass
class Report(AggregateRoot):
    """Aggregate root for analysis output reports."""

    report_id: ReportId
    session_id: SessionId
    sections: list[ReportSection] = field(default_factory=list)
    explanation_traces: list[ExplanationTrace] = field(default_factory=list)
    status: ReportStatus = field(default=ReportStatus.DRAFT)

    @classmethod
    def create(cls, session_id: SessionId) -> Report:
        """Create a new draft report for the given session."""
        report_id = ReportId.new()
        report = cls(
            id=AggregateId(str(report_id)),
            report_id=report_id,
            session_id=session_id,
        )
        report.record_event(
            ReportCreated(
                aggregate_id=str(report_id),
                metadata={
                    "report_id": str(report_id),
                    "session_id": str(session_id),
                },
                payload={
                    "report_id": str(report_id),
                    "session_id": str(session_id),
                },
            ),
        )
        return report

    def add_section(self, section: ReportSection) -> None:
        """Append a section and record a domain event."""
        if self.status == ReportStatus.COMPLETED:
            msg = "Cannot add sections to a completed report."
            raise ValueError(msg)
        self.sections.append(section)
        self.record_event(
            ReportSectionAdded(
                aggregate_id=str(self.report_id),
                metadata={"title": section.title},
                payload={
                    "report_id": str(self.report_id),
                    "title": section.title,
                    "confidence": section.confidence.value,
                },
            ),
        )

    def add_explanation_trace(self, trace: ExplanationTrace) -> None:
        """Attach an explanation trace and record a domain event."""
        if self.status == ReportStatus.COMPLETED:
            msg = "Cannot add traces to a completed report."
            raise ValueError(msg)
        self.explanation_traces.append(trace)
        self.record_event(
            ExplanationTraceAdded(
                aggregate_id=str(self.report_id),
                metadata={"steps": len(trace.reason_steps)},
                payload={
                    "report_id": str(self.report_id),
                    "reason_steps": list(trace.reason_steps),
                },
            ),
        )

    def mark_completed(self) -> None:
        """Mark the report as completed."""
        if self.status == ReportStatus.COMPLETED:
            msg = "Report is already COMPLETED."
            raise ValueError(msg)
        if not self.sections:
            msg = "Cannot complete a report without sections."
            raise ValueError(msg)
        self.status = ReportStatus.COMPLETED
