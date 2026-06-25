"""Tests for application factory."""

from __future__ import annotations

from core.application.commands import CreateAnalysisSession, GenerateText, RunAnalysis
from core.application.queries import GetAnalysisSession, ListCapabilities, ListProviders
from core.bootstrap.factory import ApplicationFactory
from core.events.replay import ReplayEngine
from core.events.store.in_memory_store import InMemoryEventStore as PublishedEventStore
from core.infrastructure.memory_event_publisher import InMemoryEventPublisher
from core.infrastructure.memory_event_store import InMemoryEventStore
from core.infrastructure.memory_repository import (
    InMemoryAnalysisSessionRepository,
    InMemoryReportRepository,
)
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork


def test_factory_creates_infrastructure_components() -> None:
    factory = ApplicationFactory()
    uow = factory.create_aggregate_unit_of_work()

    repositories = factory.create_repositories(uow)
    event_store = factory.create_aggregate_event_store(uow)
    event_publisher = factory.create_event_publisher(uow)

    assert isinstance(uow, InMemoryUnitOfWork)
    assert isinstance(repositories["analysis_session"], InMemoryAnalysisSessionRepository)
    assert isinstance(repositories["report"], InMemoryReportRepository)
    assert isinstance(event_store, InMemoryEventStore)
    assert isinstance(event_publisher, InMemoryEventPublisher)


def test_factory_creates_published_event_store_and_replay_engine() -> None:
    factory = ApplicationFactory()

    assert isinstance(factory.create_event_store(), PublishedEventStore)
    assert isinstance(factory.create_replay_engine(), ReplayEngine)


def test_factory_creates_buses_and_handlers() -> None:
    factory = ApplicationFactory()
    uow = factory.create_aggregate_unit_of_work()
    registry = factory.create_plugin_registry()
    loader = factory.create_plugin_loader(registry)
    manager = factory.create_plugin_manager(registry)
    for plugin in factory.create_analysis_stub_plugins():
        loader.load_from_instance(plugin)
    provider_registry = factory.create_provider_registry()
    provider_manager = factory.create_provider_manager(provider_registry)
    for provider in factory.create_default_providers():
        provider_registry.register(provider)
    engine = factory.create_engine(uow, manager)
    lifecycle = factory.create_engine_lifecycle_manager(engine)
    adapter = factory.create_engine_adapter(engine, lifecycle)
    handlers = factory.create_handlers(uow, adapter, manager, provider_manager)

    command_bus = factory.create_command_bus(handlers["command_handlers"])
    query_bus = factory.create_query_bus(handlers["query_handlers"])

    assert CreateAnalysisSession in handlers["command_handlers"]
    assert RunAnalysis in handlers["command_handlers"]
    assert GenerateText in handlers["command_handlers"]
    assert GetAnalysisSession in handlers["query_handlers"]
    assert ListCapabilities in handlers["query_handlers"]
    assert ListProviders in handlers["query_handlers"]
    assert len(handlers["use_cases"]) == 17
    assert "event_store" in handlers
    assert "snapshot_store" in handlers
    assert "transaction_unit_of_work" in handlers
    assert "metrics_collector" in handlers
    assert command_bus.dispatch.__name__ == "dispatch"
    assert query_bus.execute.__name__ == "execute"


def test_factory_exposes_container() -> None:
    from core.container.container import Container

    factory = ApplicationFactory()
    assert isinstance(factory.container(), Container)


def test_factory_creates_transaction_unit_of_work() -> None:
    from core.uow.in_memory import InMemoryUnitOfWork as TransactionInMemoryUnitOfWork

    factory = ApplicationFactory()
    store = factory.create_event_store()
    snapshots = factory.create_snapshot_store()
    tx_uow = factory.create_unit_of_work(store, snapshots)

    assert isinstance(tx_uow, TransactionInMemoryUnitOfWork)
