"""Tests for application registry."""

from __future__ import annotations

import pytest

from core.application.commands import CreateAnalysisSession
from core.application.queries import GetAnalysisSession
from core.bootstrap.registry import DuplicateRegistrationError, Registry, RegistryError


def test_registry_registers_and_retrieves_components() -> None:
    registry = Registry()
    command_handler = object()
    query_handler = object()
    repository = object()
    service = object()
    store = object()
    publisher = object()
    use_case = object()

    registry.register_command_handler(CreateAnalysisSession, command_handler)
    registry.register_query_handler(GetAnalysisSession, query_handler)
    registry.register_repository("analysis_session", repository)
    registry.register_service("bootstrap", service)
    registry.register_event_store("default", store)
    registry.register_event_publisher("default", publisher)
    registry.register_use_case("create_analysis_session", use_case)

    assert registry.get_command_handler(CreateAnalysisSession) is command_handler
    assert registry.get_query_handler(GetAnalysisSession) is query_handler
    assert registry.get_repository("analysis_session") is repository
    assert registry.get_service("bootstrap") is service
    assert registry.get_event_store("default") is store
    assert registry.get_event_publisher("default") is publisher
    assert registry.get_use_case("create_analysis_session") is use_case


def test_registry_prevents_duplicate_registration() -> None:
    registry = Registry()
    registry.register_repository("report", object())

    with pytest.raises(DuplicateRegistrationError):
        registry.register_repository("report", object())


def test_registry_missing_lookup_raises() -> None:
    registry = Registry()
    with pytest.raises(RegistryError, match="not registered"):
        registry.get_use_case("missing")
