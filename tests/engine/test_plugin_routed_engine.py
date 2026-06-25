"""Tests for plugin-routed stub engine execution."""

from __future__ import annotations

from uuid import uuid4

from core.application.capability_catalog import CapabilityCatalog
from core.application.command_bus import CommandBus
from core.application.commands import RunAnalysis
from core.application.handlers import RunAnalysisCommandHandler
from core.application.result import Failure, Success
from core.common.error_codes import ErrorCode
from core.application.use_cases import RunAnalysisUseCase
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.adapter import EngineAdapter
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.request import EngineRunRequest
from core.engine.stub_engine import StubEngine
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis_command(capability: str = "stub.analysis") -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=8, day=8, hour=8, minute=8),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
    )


def _request(capability: str = "stub.analysis") -> EngineRunRequest:
    user_id = UserId.new()
    session_id = SessionId.new()
    return EngineRunRequest(
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=8, day=8, hour=8, minute=8),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
    )


def _wired_run_analysis(plugin_manager: PluginManager | None = None) -> tuple[CommandBus, InMemoryUnitOfWork]:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow, plugin_manager=plugin_manager)
    engine.initialize()
    adapter = EngineAdapter(engine, EngineLifecycleManager(engine))
    capability_catalog = (
        CapabilityCatalog(plugin_manager) if plugin_manager is not None else None
    )
    bus = CommandBus()
    bus.register(
        RunAnalysis,
        RunAnalysisCommandHandler(
            RunAnalysisUseCase(
                adapter,
                plugin_manager,
                capability_catalog=capability_catalog,
            ),
        ),
    )
    return bus, uow


def test_run_analysis_routes_default_capability_to_stub_plugin() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    manager = PluginManager(registry)
    loader.load_from_instance(StubPlugin())
    manager.initialize_all()

    bus, uow = _wired_run_analysis(manager)
    result = bus.dispatch(_run_analysis_command())

    assert isinstance(result, Success)
    report = uow.reports.get(result.unwrap().report_id)
    assert report is not None
    assert report.sections[0].content == "stub placeholder"
    assert report.explanation_traces[0].reason_steps[0].startswith("PLUGIN:stub.analysis")


def test_run_analysis_missing_capability_returns_failure() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    manager = PluginManager(registry)
    loader.load_from_instance(StubPlugin())
    manager.initialize_all()

    bus, _uow = _wired_run_analysis(manager)
    result = bus.dispatch(_run_analysis_command(capability="wealth.analysis"))

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.CAPABILITY_NOT_FOUND


def test_stub_engine_without_plugin_manager_uses_fallback_content() -> None:
    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow)
    engine.initialize()
    adapter = EngineAdapter(engine, EngineLifecycleManager(engine))

    response = adapter.run_analysis(_request())
    report = uow.reports.get(response.report_id)

    assert report is not None
    assert report.sections[0].content == "Stub result only"
