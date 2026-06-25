"""Tests for composition root bootstrap."""

from __future__ import annotations

from uuid import uuid4

import pytest

from core.application.commands import (
    CompleteAnalysisSession,
    CreateAnalysisSession,
    GenerateText,
    RunAnalysis,
    StartAnalysisSession,
)
from core.application.queries import GetAnalysisSession, GetEventsByType, ListCapabilities, ListProviders
from core.application.result import Success
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.container import ContainerError
from core.bootstrap.configuration import EngineConfiguration
from core.contracts.metadata import Metadata
from core.domain.ids import UserId
from core.domain.session import SessionStatus
from core.domain.value_objects import BirthData


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def test_bootstrap_build_registers_components() -> None:
    bootstrap = Bootstrap().build()

    assert bootstrap.is_built
    assert bootstrap.container().exists("unit_of_work")
    assert bootstrap.container().exists("command_bus")
    assert bootstrap.container().exists("query_bus")
    assert bootstrap.container().exists("plugin_manager")
    assert bootstrap.container().exists("provider_manager")
    assert bootstrap.container().exists("module_registry")
    assert bootstrap.registry().has_use_case("create_analysis_session")
    assert bootstrap.registry().has_command_handler(CreateAnalysisSession)
    assert bootstrap.registry().has_command_handler(RunAnalysis)
    assert bootstrap.registry().has_command_handler(GenerateText)
    assert bootstrap.registry().has_query_handler(GetAnalysisSession)
    assert bootstrap.registry().has_query_handler(ListCapabilities)
    assert bootstrap.registry().has_query_handler(ListProviders)


def test_bootstrap_reset_clears_state() -> None:
    bootstrap = Bootstrap().build()
    bootstrap.reset()

    assert not bootstrap.is_built
    assert not bootstrap.container().exists("command_bus")


def test_bootstrap_resolve_before_build_raises() -> None:
    bootstrap = Bootstrap()
    with pytest.raises(ContainerError, match="build"):
        bootstrap.command_bus()


def test_bootstrap_command_and_query_bus_integration() -> None:
    bootstrap = Bootstrap(EngineConfiguration(environment="test")).build()
    command_bus = bootstrap.command_bus()
    query_bus = bootstrap.query_bus()

    create_result = command_bus.dispatch(
        CreateAnalysisSession(
            metadata=_metadata(),
            user_id=UserId.new(),
            birth_data=BirthData(year=1990, month=3, day=3, hour=10, minute=0),
        ),
    )
    assert isinstance(create_result, Success)
    session = create_result.unwrap()

    start_result = command_bus.dispatch(
        StartAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )
    assert isinstance(start_result, Success)
    assert start_result.unwrap().status == SessionStatus.RUNNING

    complete_result = command_bus.dispatch(
        CompleteAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )
    assert isinstance(complete_result, Success)
    assert complete_result.unwrap().status == SessionStatus.COMPLETED

    query_result = query_bus.execute(
        GetAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )
    assert isinstance(query_result, Success)
    assert query_result.unwrap().session_id == session.session_id


def test_bootstrap_use_case_event_query() -> None:
    bootstrap = Bootstrap().build()
    command_bus = bootstrap.command_bus()
    query_bus = bootstrap.query_bus()

    command_bus.dispatch(
        CreateAnalysisSession(
            metadata=_metadata(),
            user_id=UserId.new(),
            birth_data=BirthData(year=1985, month=7, day=7, hour=7, minute=7),
        ),
    )

    events_result = query_bus.execute(
        GetEventsByType(metadata=_metadata(), event_type="AnalysisSessionCreated"),
    )
    assert isinstance(events_result, Success)
    assert len(events_result.unwrap()) == 1

    use_case = bootstrap.registry().get_use_case("get_events_by_type")
    assert use_case is not None
