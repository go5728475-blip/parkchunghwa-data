"""Tests for RunAnalysis capability pre-validation."""

from __future__ import annotations

from uuid import uuid4

from core.application.capability_catalog import CapabilityCatalog
from core.application.command_bus import CommandBus
from core.application.commands import RunAnalysis
from core.application.handlers import RunAnalysisCommandHandler
from core.application.result import Failure, Success
from core.application.use_cases import RunAnalysisUseCase
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.configuration import EngineConfiguration
from core.common.error_codes import ErrorCode
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.adapter import EngineAdapter
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.stub_engine import StubEngine
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork
from core.plugin.analysis_stubs import WealthStubPlugin
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis(capability: str) -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1995, month=5, day=5, hour=5, minute=5),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
    )


def test_run_analysis_missing_capability_returns_not_found() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis("missing.capability"),
    )

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.CAPABILITY_NOT_FOUND
    assert result.error.code != ErrorCode.ENGINE_RUN_FAILED


def test_run_analysis_disabled_capability_returns_disabled() -> None:
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    loader.load_from_instance(StubPlugin())
    loader.load_from_instance(WealthStubPlugin(enabled=False))
    manager = PluginManager(registry)
    manager.initialize_all()
    catalog = CapabilityCatalog(manager)

    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow, plugin_manager=manager)
    engine.initialize()
    adapter = EngineAdapter(engine, EngineLifecycleManager(engine))
    bus = CommandBus()
    bus.register(
        RunAnalysis,
        RunAnalysisCommandHandler(
            RunAnalysisUseCase(adapter, manager, capability_catalog=catalog),
        ),
    )

    result = bus.dispatch(_run_analysis("wealth.analysis"))

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.CAPABILITY_DISABLED
    assert result.error.code != ErrorCode.ENGINE_RUN_FAILED


def test_run_analysis_unsupported_capability_returns_not_supported() -> None:
    bootstrap = Bootstrap(
        EngineConfiguration(supported_capabilities=("stub.analysis",)),
    ).build()
    result = bootstrap.command_bus().dispatch(_run_analysis("wealth.analysis"))

    assert isinstance(result, Failure)
    assert result.error.code == ErrorCode.CAPABILITY_NOT_SUPPORTED
    assert result.error.code != ErrorCode.ENGINE_RUN_FAILED


def test_run_analysis_valid_capability_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(_run_analysis("wealth.analysis"))

    assert isinstance(result, Success)
    report = bootstrap.unit_of_work().reports.get(result.unwrap().report_id)
    assert report is not None
    assert report.sections[0].content == "wealth placeholder"
