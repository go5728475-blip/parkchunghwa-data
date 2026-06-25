"""Tests for engine kernel lifecycle."""

from __future__ import annotations

import pytest

from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.kernel import EngineKernel, EngineKernelError
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus


def _request() -> EngineRunRequest:
    user_id = UserId.new()
    session_id = SessionId.new()
    return EngineRunRequest(
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=0, minute=0),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


class _SuccessfulKernel(EngineKernel):
    def _execute_run(self, request: EngineRunRequest) -> EngineRunResponse:
        return EngineRunResponse(
            session_id=request.session_id,
            status=EngineStatus.COMPLETED,
            summary="ok",
        )


class _FailingKernel(EngineKernel):
    def _execute_run(self, request: EngineRunRequest) -> EngineRunResponse:
        msg = "simulated failure"
        raise RuntimeError(msg)


def test_engine_status_transitions() -> None:
    kernel = _SuccessfulKernel()
    assert kernel.status() == EngineStatus.IDLE

    kernel.initialize()
    assert kernel.status() == EngineStatus.READY

    response = kernel.run(_request())
    assert kernel.status() == EngineStatus.COMPLETED
    assert response.status == EngineStatus.COMPLETED

    kernel.shutdown()
    assert kernel.status() == EngineStatus.IDLE


def test_run_before_initialize_raises() -> None:
    kernel = _SuccessfulKernel()
    with pytest.raises(EngineKernelError, match="READY"):
        kernel.run(_request())


def test_failed_run_sets_failed_status() -> None:
    kernel = _FailingKernel()
    kernel.initialize()
    response = kernel.run(_request())

    assert kernel.status() == EngineStatus.FAILED
    assert response.status == EngineStatus.FAILED
    assert response.errors[0].code == "ENGINE_RUN_FAILED"
