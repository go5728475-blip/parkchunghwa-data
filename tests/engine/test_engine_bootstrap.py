"""Tests for engine bootstrap wiring."""

from __future__ import annotations

from core.bootstrap.bootstrap import Bootstrap, CONTAINER_KEY_ENGINE
from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.request import EngineRunRequest
from core.engine.stub_engine import StubEngine
from core.engine.status import EngineStatus


def _request() -> EngineRunRequest:
    user_id = UserId.new()
    session_id = SessionId.new()
    return EngineRunRequest(
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1989, month=9, day=9, hour=9, minute=9),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


def test_bootstrap_resolves_engine() -> None:
    bootstrap = Bootstrap().build()
    engine = bootstrap.container().resolve(CONTAINER_KEY_ENGINE)

    assert isinstance(engine, StubEngine)
    assert bootstrap.registry().has_service("engine")
    assert bootstrap.engine() is engine


def test_bootstrap_engine_run_through_container() -> None:
    bootstrap = Bootstrap().build()
    engine = bootstrap.container().resolve(CONTAINER_KEY_ENGINE)
    uow = bootstrap.unit_of_work()

    response = engine.run(_request())

    assert response.report_id is not None
    assert uow.reports.get(response.report_id) is not None
    assert engine.status() == EngineStatus.COMPLETED
