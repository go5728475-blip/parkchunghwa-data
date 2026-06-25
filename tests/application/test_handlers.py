"""Tests for application handlers and bus integration."""

from __future__ import annotations

from uuid import uuid4

from core.application.command_bus import CommandBus
from core.application.commands import CreateAnalysisSession
from core.application.handlers import (
    CreateAnalysisSessionHandler,
    GetAnalysisSessionHandler,
)
from core.application.queries import GetAnalysisSession
from core.application.query_bus import QueryBus
from core.application.result import Success
from core.application.use_cases import (
    CreateAnalysisSessionUseCase,
    GetAnalysisSessionUseCase,
)
from core.contracts.metadata import Metadata
from core.domain.ids import SessionId, UserId
from core.domain.value_objects import BirthData
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


def test_create_analysis_session_handler_delegates_to_use_case() -> None:
    uow = InMemoryUnitOfWork()
    handler = CreateAnalysisSessionHandler(CreateAnalysisSessionUseCase(uow))
    command = CreateAnalysisSession(
        metadata=_metadata(),
        user_id=UserId.new(),
        birth_data=BirthData(year=1990, month=5, day=10, hour=12, minute=0),
    )

    result = handler(command)

    assert isinstance(result, Success)
    assert uow.sessions.get(result.unwrap().session_id) is not None


def test_handler_bus_integration() -> None:
    uow = InMemoryUnitOfWork()
    command_bus = CommandBus()
    query_bus = QueryBus()

    command_bus.register(
        CreateAnalysisSession,
        CreateAnalysisSessionHandler(CreateAnalysisSessionUseCase(uow)),
    )
    query_bus.register(
        GetAnalysisSession,
        GetAnalysisSessionHandler(GetAnalysisSessionUseCase(uow)),
    )

    create_result = command_bus.dispatch(
        CreateAnalysisSession(
            metadata=_metadata(),
            user_id=UserId.new(),
            birth_data=BirthData(year=1991, month=1, day=1, hour=0, minute=0),
        ),
    )
    session = create_result.unwrap()
    query_result = query_bus.execute(
        GetAnalysisSession(metadata=_metadata(), session_id=session.session_id),
    )

    assert isinstance(query_result, Success)
    assert query_result.unwrap().session_id == session.session_id
