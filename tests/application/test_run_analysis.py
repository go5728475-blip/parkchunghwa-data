"""Tests for RunAnalysis application flow."""

from __future__ import annotations

from uuid import uuid4

from core.application.command_bus import CommandBus
from core.application.commands import RunAnalysis
from core.application.handlers import RunAnalysisCommandHandler
from core.application.result import Failure, Success
from core.application.use_cases import RunAnalysisUseCase
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId
from core.domain.models import TraceStep
from core.domain.value_objects import BirthData, EngineContext
from core.engine.adapter import EngineAdapter
from core.engine.kernel import EngineKernel
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus
from core.engine.stub_engine import StubEngine
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis_command() -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=6, day=15, hour=10, minute=30),
        context=EngineContext(user_id=user_id, session_id=session_id),
    )


def _adapter(engine: StubEngine | EngineKernel) -> EngineAdapter:
    return EngineAdapter(engine, EngineLifecycleManager(engine))


def test_run_analysis_command_dispatch_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(_run_analysis_command())

    assert isinstance(result, Success)
    response = result.unwrap()
    assert response.status == EngineStatus.COMPLETED
    assert response.report_id is not None
    report = bootstrap.unit_of_work().reports.get(response.report_id)
    assert report is not None
    assert "stub placeholder" in report.sections[0].content


def test_run_analysis_passes_capability_to_engine() -> None:
    bootstrap = Bootstrap().build()
    user_id = UserId.new()
    session_id = SessionId.new()
    command = RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1991, month=7, day=7, hour=7, minute=7),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability="stub.analysis",
    )
    result = bootstrap.command_bus().dispatch(command)

    assert isinstance(result, Success)
    report = bootstrap.unit_of_work().reports.get(result.unwrap().report_id)
    assert report is not None
    assert "stub placeholder" in report.sections[0].content


def test_run_analysis_passes_provider_id_to_engine() -> None:
    bootstrap = Bootstrap().build()
    user_id = UserId.new()
    session_id = SessionId.new()
    command = RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1993, month=9, day=9, hour=9, minute=9),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability="wealth.analysis",
        provider_id=ProviderId(value="openai.stub"),
    )
    result = bootstrap.command_bus().dispatch(command)

    assert isinstance(result, Success)
    response = result.unwrap()
    report = bootstrap.unit_of_work().reports.get(response.report_id)
    assert report is not None
    assert report.sections[0].content == "wealth placeholder"
    assert "openai stub placeholder response" in report.sections[1].content
    assert response.analysis_result is not None
    steps = [entry.step for entry in response.analysis_result.trace]
    assert steps[0] is TraceStep.PLUGIN
    assert steps[1] is TraceStep.PROVIDER
    assert steps[2] is TraceStep.REPORT
    assert response.analysis_result.trace[0].source == "wealth.analysis"
    assert str(response.analysis_result.trace[1].source) == "openai.stub"


def test_run_analysis_consecutive_dispatch_success() -> None:
    bootstrap = Bootstrap().build()
    command_bus = bootstrap.command_bus()

    first = command_bus.dispatch(_run_analysis_command())
    second = command_bus.dispatch(_run_analysis_command())

    assert isinstance(first, Success)
    assert isinstance(second, Success)
    assert first.unwrap().report_id is not None
    assert second.unwrap().report_id is not None


def test_run_analysis_stores_events_in_event_store() -> None:
    bootstrap = Bootstrap().build()
    uow = bootstrap.unit_of_work()

    bootstrap.command_bus().dispatch(_run_analysis_command())

    assert uow.event_store.load_by_event_type("ReportCreated")
    assert uow.event_store.load_by_event_type("AnalysisSessionCreated")
    assert uow.event_store.load_by_event_type("ReportSectionAdded")


def test_run_analysis_fails_when_engine_running() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    engine.initialize()
    engine._status = EngineStatus.RUNNING
    handler = RunAnalysisCommandHandler(RunAnalysisUseCase(_adapter(engine)))
    bus = CommandBus()
    bus.register(RunAnalysis, handler)

    result = bus.dispatch(_run_analysis_command())

    assert isinstance(result, Failure)
    assert result.error.code == "ENGINE_NOT_READY"


def test_run_analysis_fails_when_engine_run_fails() -> None:
    uow = InMemoryUnitOfWork()

    class _FailingEngine(EngineKernel):
        def _execute_run(self, request: EngineRunRequest) -> EngineRunResponse:
            msg = "stub failure"
            raise RuntimeError(msg)

    engine = _FailingEngine()
    engine.initialize()
    handler = RunAnalysisCommandHandler(RunAnalysisUseCase(_adapter(engine)))
    bus = CommandBus()
    bus.register(RunAnalysis, handler)

    result = bus.dispatch(_run_analysis_command())

    assert isinstance(result, Failure)
    assert result.error.code == "ENGINE_RUN_FAILED"
