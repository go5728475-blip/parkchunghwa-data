"""Tests for application use cases."""

from __future__ import annotations

from uuid import uuid4

from core.application.commands import (
    AddExplanationTrace,
    AddReportSection,
    CompleteAnalysisSession,
    CompleteReport,
    CreateAnalysisSession,
    CreateReport,
    FailAnalysisSession,
    StartAnalysisSession,
)
from core.application.queries import (
    GetAnalysisSession,
    GetEventsByAggregate,
    GetEventsByType,
    GetReport,
    ListReports,
)
from core.application.result import Failure, Success
from core.application.use_cases import (
    AddExplanationTraceUseCase,
    AddReportSectionUseCase,
    CompleteAnalysisSessionUseCase,
    CompleteReportUseCase,
    CreateAnalysisSessionUseCase,
    CreateReportUseCase,
    FailAnalysisSessionUseCase,
    GetAnalysisSessionUseCase,
    GetEventsByAggregateUseCase,
    GetEventsByTypeUseCase,
    GetReportUseCase,
    ListReportsUseCase,
    StartAnalysisSessionUseCase,
)
from core.contracts.metadata import Metadata
from core.domain.ids import ReportId, SessionId, UserId
from core.domain.session import SessionStatus
from core.domain.value_objects import (
    BirthData,
    ConfidenceScore,
    ExplanationTrace,
    ReportSection,
)
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _create_session(uow: InMemoryUnitOfWork):
    result = CreateAnalysisSessionUseCase(uow).execute(
        CreateAnalysisSession(
            metadata=_metadata(),
            user_id=UserId.new(),
            birth_data=BirthData(year=1990, month=1, day=1, hour=0, minute=0),
        ),
    )
    return result.unwrap()


def test_create_analysis_session_use_case() -> None:
    uow = InMemoryUnitOfWork()
    result = CreateAnalysisSessionUseCase(uow).execute(
        CreateAnalysisSession(
            metadata=_metadata(),
            user_id=UserId.new(),
            birth_data=BirthData(year=1988, month=6, day=15, hour=9, minute=30),
        ),
    )

    assert isinstance(result, Success)
    session = result.unwrap()
    assert uow.sessions.get(session.session_id) is session
    assert len(uow.event_store.load_all()) == 1


def test_session_start_complete_fail_use_cases() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)

    start_result = StartAnalysisSessionUseCase(uow).execute(
        StartAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )
    assert isinstance(start_result, Success)
    assert start_result.unwrap().status == SessionStatus.RUNNING

    complete_result = CompleteAnalysisSessionUseCase(uow).execute(
        CompleteAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )
    assert isinstance(complete_result, Success)
    assert complete_result.unwrap().status == SessionStatus.COMPLETED

    uow2 = InMemoryUnitOfWork()
    failed_session = _create_session(uow2)
    fail_result = FailAnalysisSessionUseCase(uow2).execute(
        FailAnalysisSession(
            metadata=_metadata(),
            session_id=failed_session.session_id,
            reason="engine timeout",
        ),
    )
    assert isinstance(fail_result, Success)
    assert fail_result.unwrap().status == SessionStatus.FAILED


def test_create_report_use_case() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)

    result = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    )

    assert isinstance(result, Success)
    report = result.unwrap()
    assert uow.reports.get(report.report_id) is report


def test_add_report_section_use_case() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)
    report = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    ).unwrap()

    result = AddReportSectionUseCase(uow).execute(
        AddReportSection(
            metadata=_metadata(),
            report_id=report.report_id,
            section=ReportSection(
                title="Summary",
                content="Body text",
                confidence=ConfidenceScore(value=0.85),
            ),
        ),
    )

    assert isinstance(result, Success)
    assert len(result.unwrap().sections) == 1


def test_add_explanation_trace_use_case() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)
    report = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    ).unwrap()

    result = AddExplanationTraceUseCase(uow).execute(
        AddExplanationTrace(
            metadata=_metadata(),
            report_id=report.report_id,
            trace=ExplanationTrace(reason_steps=("step-1", "step-2")),
        ),
    )

    assert isinstance(result, Success)
    assert len(result.unwrap().explanation_traces) == 1


def test_complete_report_use_case() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)
    report = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    ).unwrap()
    AddReportSectionUseCase(uow).execute(
        AddReportSection(
            metadata=_metadata(),
            report_id=report.report_id,
            section=ReportSection(
                title="Summary",
                content="Body",
                confidence=ConfidenceScore(value=0.7),
            ),
        ),
    )

    result = CompleteReportUseCase(uow).execute(
        CompleteReport(metadata=_metadata(), report_id=report.report_id),
    )

    assert isinstance(result, Success)
    assert result.unwrap().status.value == "COMPLETED"


def test_complete_report_without_section_fails() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)
    report = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    ).unwrap()

    result = CompleteReportUseCase(uow).execute(
        CompleteReport(metadata=_metadata(), report_id=report.report_id),
    )

    assert isinstance(result, Failure)
    assert result.error.code == "DOMAIN_VALIDATION_ERROR"


def test_get_analysis_session_query() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)

    found = GetAnalysisSessionUseCase(uow).execute(
        GetAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )
    missing = GetAnalysisSessionUseCase(uow).execute(
        GetAnalysisSession(metadata=_metadata(), session_id=SessionId.new()),
    )

    assert isinstance(found, Success)
    assert found.unwrap().session_id == session.session_id
    assert isinstance(missing, Failure)
    assert missing.error.code == "NOT_FOUND"


def test_get_report_query() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)
    report = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    ).unwrap()

    found = GetReportUseCase(uow).execute(
        GetReport(metadata=_metadata(), report_id=report.report_id),
    )
    missing = GetReportUseCase(uow).execute(
        GetReport(metadata=_metadata(), report_id=ReportId.new()),
    )

    assert isinstance(found, Success)
    assert found.unwrap().report_id == report.report_id
    assert isinstance(missing, Failure)


def test_list_reports_query() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)
    report = CreateReportUseCase(uow).execute(
        CreateReport(metadata=_metadata(), session_id=session.session_id),
    ).unwrap()

    all_reports = ListReportsUseCase(uow).execute(
        ListReports(metadata=_metadata()),
    )
    filtered = ListReportsUseCase(uow).execute(
        ListReports(metadata=_metadata(), session_id=session.session_id),
    )
    empty = ListReportsUseCase(uow).execute(
        ListReports(metadata=_metadata(), session_id=SessionId.new()),
    )

    assert isinstance(all_reports, Success)
    assert len(all_reports.unwrap()) == 1
    assert isinstance(filtered, Success)
    assert filtered.unwrap()[0].report_id == report.report_id
    assert isinstance(empty, Success)
    assert empty.unwrap() == []


def test_event_queries_by_aggregate_and_type() -> None:
    uow = InMemoryUnitOfWork()
    session = _create_session(uow)

    by_aggregate = GetEventsByAggregateUseCase(uow).execute(
        GetEventsByAggregate(
            metadata=_metadata(),
            aggregate_id=str(session.session_id),
        ),
    )
    by_type = GetEventsByTypeUseCase(uow).execute(
        GetEventsByType(
            metadata=_metadata(),
            event_type="AnalysisSessionCreated",
        ),
    )

    assert isinstance(by_aggregate, Success)
    assert len(by_aggregate.unwrap()) == 1
    assert isinstance(by_type, Success)
    assert by_type.unwrap()[0].event_type == "AnalysisSessionCreated"
