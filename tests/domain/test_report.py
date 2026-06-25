"""Tests for report aggregate."""

from __future__ import annotations

import pytest

from core.domain.events import (
    ExplanationTraceAdded,
    ReportCreated,
    ReportSectionAdded,
)
from core.domain.ids import SessionId
from core.domain.report import Report, ReportStatus
from core.domain.value_objects import ConfidenceScore, ExplanationTrace, ReportSection


def _section() -> ReportSection:
    return ReportSection(
        title="Summary",
        content="Content body",
        confidence=ConfidenceScore(value=0.8),
    )


def _trace() -> ExplanationTrace:
    return ExplanationTrace(reason_steps=("step-1", "step-2"))


def test_report_create_records_event() -> None:
    report = Report.create(session_id=SessionId.new())
    events = report.pull_events()
    assert len(events) == 1
    assert isinstance(events[0], ReportCreated)


def test_report_add_section_and_trace_record_events() -> None:
    report = Report.create(session_id=SessionId.new())
    report.pull_events()
    report.add_section(_section())
    report.add_explanation_trace(_trace())
    events = report.pull_events()
    assert any(isinstance(event, ReportSectionAdded) for event in events)
    assert any(isinstance(event, ExplanationTraceAdded) for event in events)


def test_report_mark_completed_requires_section() -> None:
    report = Report.create(session_id=SessionId.new())
    with pytest.raises(ValueError, match="without sections"):
        report.mark_completed()


def test_report_mark_completed_succeeds_with_section() -> None:
    report = Report.create(session_id=SessionId.new())
    report.add_section(_section())
    report.mark_completed()
    assert report.status == ReportStatus.COMPLETED
