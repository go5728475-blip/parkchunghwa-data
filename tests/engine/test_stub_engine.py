"""Tests for stub engine."""

from __future__ import annotations

from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.request import EngineRunRequest
from core.engine.status import EngineStatus
from core.engine.stub_engine import StubEngine
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def _request() -> EngineRunRequest:
    user_id = UserId.new()
    session_id = SessionId.new()
    return EngineRunRequest(
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1992, month=4, day=4, hour=4, minute=4),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


def test_stub_engine_run_returns_report_id() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    engine.initialize()

    response = engine.run(_request())

    assert response.report_id is not None
    assert response.summary == "Stub result only"
    assert response.explanation_trace is not None
    assert engine.status() == EngineStatus.COMPLETED


def test_stub_engine_persists_report_and_events() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    engine.initialize()

    response = engine.run(_request())

    report = uow.reports.get(response.report_id)
    assert report is not None
    assert len(report.sections) == 1
    assert len(report.explanation_traces) == 1

    events = uow.event_store.load_by_event_type("ReportCreated")
    assert len(events) == 1
    assert uow.event_store.load_by_event_type("ReportSectionAdded")
    assert uow.event_store.load_by_event_type("ExplanationTraceAdded")
