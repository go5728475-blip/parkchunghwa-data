"""Tests for analysis capability routing through RunAnalysis."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.commands import RunAnalysis
from core.application.result import Success
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData, EngineContext
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def _run_analysis(capability: str) -> RunAnalysis:
    user_id = UserId.new()
    session_id = SessionId.new()
    return RunAnalysis(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1993, month=3, day=3, hour=3, minute=3),
        context=EngineContext(user_id=user_id, session_id=session_id),
        capability=capability,
    )


def _bootstrap_with_all_stubs() -> Bootstrap:
    return Bootstrap().build()


@pytest.mark.parametrize(
    ("capability", "placeholder"),
    [
        ("master_lock.analysis", "master lock placeholder"),
        ("wealth.analysis", "wealth placeholder"),
        ("career.analysis", "career placeholder"),
        ("relationship.analysis", "relationship placeholder"),
    ],
)
def test_run_analysis_routes_capability_to_matching_stub(
    capability: str,
    placeholder: str,
) -> None:
    bootstrap = _bootstrap_with_all_stubs()
    result = bootstrap.command_bus().dispatch(_run_analysis(capability))

    assert isinstance(result, Success)
    report = bootstrap.unit_of_work().reports.get(result.unwrap().report_id)
    assert report is not None
    assert placeholder in report.sections[0].content


def test_factory_registers_five_analysis_stub_plugins() -> None:
    factory = ApplicationFactory()
    registry = PluginRegistry()
    loader = PluginLoader(registry)
    plugins = factory.create_analysis_stub_plugins()

    assert len(plugins) == 5
    for plugin in plugins:
        loader.load_from_instance(plugin)

    manager = PluginManager(registry)
    manager.initialize_all()
    assert len(registry.list()) == 5
