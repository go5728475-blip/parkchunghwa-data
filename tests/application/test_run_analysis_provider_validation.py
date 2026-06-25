"""Tests for RunAnalysis provider_id pre-validation."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.capability_catalog import CapabilityCatalog
from core.application.command_bus import CommandBus
from core.application.commands import RunAnalysis
from core.application.handlers import RunAnalysisCommandHandler
from core.application.result import Failure, Success
from core.application.use_cases import RunAnalysisUseCase
from core.bootstrap.bootstrap import Bootstrap
from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.engine.adapter import EngineAdapter
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.stub_engine import StubEngine
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork
from core.provider.manager import ProviderManager
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry
from core.plugin.stub import StubPlugin
from core.provider.named_stubs import OpenAIStubProvider
from core.provider.registry import ProviderRegistry
from core.provider.stub import StubProvider


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis_command(
    *,
    capability: str = "stub.analysis",
    provider_id: ProviderId | None = None,
) -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1994, month=5, day=5, hour=5, minute=5),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
        provider_id=provider_id,
    )


def test_run_analysis_without_provider_id_uses_plugin_flow() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(_run_analysis_command())

    assert isinstance(result, Success)
    report = bootstrap.unit_of_work().reports.get(result.unwrap().report_id)
    assert report is not None
    assert report.sections[0].content == "stub placeholder"


def test_run_analysis_with_valid_provider_id_success() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis_command(provider_id=OpenAIStubProvider.provider_id()),
    )

    assert isinstance(result, Success)
    report = bootstrap.unit_of_work().reports.get(result.unwrap().report_id)
    assert report is not None
    assert report.sections[0].content == "stub placeholder"
    assert "openai stub placeholder response" in report.sections[1].content


def test_run_analysis_missing_provider_id_failure() -> None:
    bootstrap = Bootstrap().build()
    result = bootstrap.command_bus().dispatch(
        _run_analysis_command(provider_id=ProviderId(value="missing.provider")),
    )

    assert isinstance(result, Failure)
    assert result.error.code == "PROVIDER_NOT_FOUND"
    assert "missing.provider" in result.error.message


def test_run_analysis_disabled_provider_id_failure() -> None:
    provider_registry = ProviderRegistry()
    provider_registry.register(StubProvider(enabled=False))
    provider_manager = ProviderManager(provider_registry)

    plugin_registry = PluginRegistry()
    plugin_loader = PluginLoader(plugin_registry)
    plugin_loader.load_from_instance(StubPlugin())
    plugin_manager = PluginManager(plugin_registry)
    plugin_manager.initialize_all()

    uow = InMemoryUnitOfWork()
    engine = StubEngine(uow, plugin_manager=plugin_manager)
    engine.initialize()
    adapter = EngineAdapter(engine, EngineLifecycleManager(engine))
    bus = CommandBus()
    bus.register(
        RunAnalysis,
        RunAnalysisCommandHandler(
            RunAnalysisUseCase(
                adapter,
                plugin_manager,
                provider_manager,
                CapabilityCatalog(plugin_manager),
            ),
        ),
    )

    result = bus.dispatch(
        _run_analysis_command(provider_id=StubProvider.provider_id()),
    )

    assert isinstance(result, Failure)
    assert result.error.code == "PROVIDER_DISABLED"
    assert "stub.provider" in result.error.message


def test_run_analysis_blank_provider_id_command_validation() -> None:
    with pytest.raises(ValueError, match="empty"):
        ProviderId(value="   ")


def test_run_analysis_command_rejects_blank_provider_id_value() -> None:
    user_id = UserId.new()
    session_id = SessionId.new()
    with pytest.raises(ValueError, match="empty"):
        RunAnalysis(
            metadata=_metadata(),
            session_id=session_id,
            user_id=user_id,
            birth_data=BirthData(year=1994, month=5, day=5, hour=5, minute=5),
            context=EngineContext(user_id=user_id, session_id=session_id),
            provider_id=ProviderId(value="   "),
        )
