"""Tests for engine lifecycle manager."""

from __future__ import annotations

import pytest

from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.kernel import EngineKernel
from core.engine.lifecycle import EngineLifecycleError, EngineLifecycleManager
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus
from core.engine.stub_engine import StubEngine
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def _request() -> EngineRunRequest:
    user_id = UserId.new()
    session_id = SessionId.new()
    return EngineRunRequest(
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=2, day=2, hour=2, minute=2),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


def test_lifecycle_run_from_idle() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    lifecycle = EngineLifecycleManager(engine)

    response = lifecycle.run_with_lifecycle(_request())

    assert response.report_id is not None
    assert engine.status() is EngineStatus.COMPLETED


def test_lifecycle_rerun_after_completed() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    lifecycle = EngineLifecycleManager(engine)

    lifecycle.run_with_lifecycle(_request())
    response = lifecycle.run_with_lifecycle(_request())

    assert response.report_id is not None
    assert engine.status() is EngineStatus.COMPLETED


def test_lifecycle_rerun_after_failed() -> None:
    class _FailingOnceEngine(EngineKernel):
        def __init__(self) -> None:
            super().__init__()
            self._fail_next = True

        def _execute_run(self, request: EngineRunRequest) -> EngineRunResponse:
            if self._fail_next:
                self._fail_next = False
                msg = "temporary failure"
                raise RuntimeError(msg)
            return EngineRunResponse(
                session_id=request.session_id,
                status=EngineStatus.COMPLETED,
                summary="recovered",
            )

    engine = _FailingOnceEngine()
    lifecycle = EngineLifecycleManager(engine)

    failed = lifecycle.run_with_lifecycle(_request())
    assert failed.status is EngineStatus.FAILED

    recovered = lifecycle.run_with_lifecycle(_request())
    assert recovered.status is EngineStatus.COMPLETED
    assert engine.status() is EngineStatus.COMPLETED


def test_lifecycle_fails_when_running() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    engine.initialize()
    engine._status = EngineStatus.RUNNING
    lifecycle = EngineLifecycleManager(engine)

    with pytest.raises(EngineLifecycleError, match="running"):
        lifecycle.ensure_ready()
