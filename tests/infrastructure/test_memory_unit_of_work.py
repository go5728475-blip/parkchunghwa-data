"""Tests for in-memory unit of work."""

from __future__ import annotations

from core.domain.ids import SessionId, UserId
from core.domain.report import Report
from core.domain.session import AnalysisSession
from core.domain.value_objects import BirthData, ConfidenceScore, EngineContext, ReportSection
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def _session() -> AnalysisSession:
    user_id = UserId.new()
    session_id = SessionId.new()
    return AnalysisSession.create(
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=0, minute=0),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


def test_unit_of_work_commit_persists_and_publishes_events() -> None:
    uow = InMemoryUnitOfWork()
    session = _session()
    report = Report.create(session_id=session.session_id)
    report.add_section(
        ReportSection(
            title="Summary",
            content="Body",
            confidence=ConfidenceScore(value=0.9),
        ),
    )

    uow.register_new(session)
    uow.register_new(report)

    uow.commit()

    assert uow.sessions.get(session.session_id) is session
    assert uow.reports.get(report.report_id) is report
    assert len(uow.event_store.load_all()) == 3
    assert len(uow.event_publisher.published_events) == 3
    assert session.domain_events == []
    assert report.domain_events == []


def test_unit_of_work_collect_events_tracks_dirty_aggregate() -> None:
    uow = InMemoryUnitOfWork()
    session = _session()
    session.pull_events()
    uow.sessions.save(session)

    session.mark_running()
    uow.register_dirty(session)
    uow.commit()

    assert uow.event_store.load_all() == []
    assert uow.event_publisher.published_events == []


def test_unit_of_work_rollback_does_not_store_or_publish() -> None:
    uow = InMemoryUnitOfWork()
    session = _session()

    uow.register_new(session)
    uow.rollback()

    assert uow.sessions.get(session.session_id) is None
    assert uow.event_store.load_all() == []
    assert uow.event_publisher.published_events == []
    assert session.domain_events == []
