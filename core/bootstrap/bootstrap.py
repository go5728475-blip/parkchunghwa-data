"""Composition root bootstrap."""

from __future__ import annotations

from typing import Any

from core.application.command_bus import CommandBus
from core.application.query_bus import QueryBus
from core.bootstrap.configuration import EngineConfiguration
from core.bootstrap.factory import ApplicationFactory, register_certified_plugin_registry
from core.bootstrap.registry import Registry
from core.container.container import Container
from core.container.errors import ContainerError
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.stub_engine import StubEngine
from core.events.in_memory_bus import InMemoryEventBus
from core.events.snapshot.in_memory_store import InMemorySnapshotStore
from core.events.store.in_memory_store import InMemoryEventStore as PublishedEventStore
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork
from core.metrics.in_memory import InMemoryMetricsCollector
from core.modules.bootstrap import boot_modules, create_module_registry, shutdown_modules
from core.modules.loader.manager import LoaderManager
from core.modules.registry import ModuleRegistry
from core.plugin.manager import PluginManager
from core.provider.manager import ProviderManager
from core.uow.interfaces import IUnitOfWork

CONTAINER_KEY_UNIT_OF_WORK = "unit_of_work"
CONTAINER_KEY_COMMAND_BUS = "command_bus"
CONTAINER_KEY_QUERY_BUS = "query_bus"
CONTAINER_KEY_EVENT_STORE = "event_store"
CONTAINER_KEY_EVENT_PUBLISHER = "event_publisher"
CONTAINER_KEY_SESSION_REPOSITORY = "analysis_session_repository"
CONTAINER_KEY_REPORT_REPOSITORY = "report_repository"
CONTAINER_KEY_ENGINE = "engine"
CONTAINER_KEY_ENGINE_ADAPTER = "engine_adapter"
CONTAINER_KEY_ENGINE_LIFECYCLE = "engine_lifecycle"
CONTAINER_KEY_PLUGIN_MANAGER = "plugin_manager"
CONTAINER_KEY_PROVIDER_MANAGER = "provider_manager"
CONTAINER_KEY_EVENT_BUS = "event_bus"
CONTAINER_KEY_PUBLISHED_EVENT_STORE = "published_event_store"
CONTAINER_KEY_SNAPSHOT_STORE = "snapshot_store"
CONTAINER_KEY_TRANSACTION_UNIT_OF_WORK = "transaction_unit_of_work"
CONTAINER_KEY_METRICS_COLLECTOR = "metrics_collector"
CONTAINER_KEY_MODULE_REGISTRY = "module_registry"
CONTAINER_KEY_LOADER_MANAGER = "loader_manager"
CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY = "certified_plugin_registry"


class Bootstrap:
    """Builds and exposes the fully wired application graph."""

    def __init__(self, configuration: EngineConfiguration | None = None) -> None:
        self._configuration = configuration or EngineConfiguration.default()
        self._container = Container()
        self._registry = Registry()
        self._module_registry = create_module_registry()
        self._factory = ApplicationFactory(self._configuration, self._container)
        self._built = False

    def build(self) -> Bootstrap:
        """Wire repositories, buses, handlers, and infrastructure."""
        self.reset()

        boot_modules(self._container, self._module_registry)

        unit_of_work = self._factory.create_aggregate_unit_of_work()
        repositories = self._factory.create_repositories(unit_of_work)
        event_store = self._factory.create_aggregate_event_store(unit_of_work)
        event_publisher = self._factory.create_event_publisher(unit_of_work)
        plugin_registry = self._factory.create_plugin_registry()
        plugin_loader = self._factory.create_plugin_loader(plugin_registry)
        plugin_manager = self._factory.create_plugin_manager(plugin_registry)
        for plugin in self._factory.create_analysis_stub_plugins():
            plugin_loader.load_from_instance(plugin)
        plugin_manager.initialize_all()
        provider_registry = self._factory.create_provider_registry()
        provider_manager = self._factory.create_provider_manager(provider_registry)
        for provider in self._factory.create_default_providers():
            provider_registry.register(provider)
        provider_manager.initialize_all()
        engine = self._factory.create_engine(unit_of_work, plugin_manager)
        lifecycle_manager = self._factory.create_engine_lifecycle_manager(engine)
        engine_adapter = self._factory.create_engine_adapter(engine, lifecycle_manager)
        handlers = self._factory.create_handlers(
            unit_of_work,
            engine_adapter,
            plugin_manager,
            provider_manager,
        )

        self._registry.register_repository("analysis_session", repositories["analysis_session"])
        self._registry.register_repository("report", repositories["report"])
        self._registry.register_event_store("default", event_store)
        self._registry.register_event_publisher("default", event_publisher)

        for name, use_case in handlers["use_cases"].items():
            self._registry.register_use_case(name, use_case)

        for command_type, handler in handlers["command_handlers"].items():
            self._registry.register_command_handler(command_type, handler)

        for query_type, handler in handlers["query_handlers"].items():
            self._registry.register_query_handler(query_type, handler)

        command_bus = self._factory.create_command_bus(handlers["command_handlers"])
        query_bus = self._factory.create_query_bus(handlers["query_handlers"])

        self._container.register_singleton(CONTAINER_KEY_UNIT_OF_WORK, unit_of_work)
        self._container.register_singleton(CONTAINER_KEY_COMMAND_BUS, command_bus)
        self._container.register_singleton(CONTAINER_KEY_QUERY_BUS, query_bus)
        self._container.register_singleton(CONTAINER_KEY_EVENT_STORE, event_store)
        self._container.register_singleton(CONTAINER_KEY_EVENT_PUBLISHER, event_publisher)
        self._container.register_singleton(
            CONTAINER_KEY_SESSION_REPOSITORY,
            repositories["analysis_session"],
        )
        self._container.register_singleton(
            CONTAINER_KEY_REPORT_REPOSITORY,
            repositories["report"],
        )
        self._container.register_singleton(CONTAINER_KEY_ENGINE, engine)
        self._container.register_singleton(CONTAINER_KEY_ENGINE_ADAPTER, engine_adapter)
        self._container.register_singleton(CONTAINER_KEY_ENGINE_LIFECYCLE, lifecycle_manager)
        self._registry.register_service("engine", engine)
        self._registry.register_service("engine_adapter", engine_adapter)
        self._registry.register_service("engine_lifecycle", lifecycle_manager)
        self._container.register_singleton(CONTAINER_KEY_PLUGIN_MANAGER, plugin_manager)
        self._registry.register_service("plugin_manager", plugin_manager)
        self._container.register_singleton(CONTAINER_KEY_PROVIDER_MANAGER, provider_manager)
        self._registry.register_service("provider_manager", provider_manager)
        self._container.register_singleton(CONTAINER_KEY_EVENT_BUS, handlers["event_bus"])
        self._registry.register_service("event_bus", handlers["event_bus"])
        self._container.register_singleton(
            CONTAINER_KEY_PUBLISHED_EVENT_STORE,
            handlers["event_store"],
        )
        self._registry.register_service("published_event_store", handlers["event_store"])
        self._container.register_singleton(
            CONTAINER_KEY_SNAPSHOT_STORE,
            handlers["snapshot_store"],
        )
        self._registry.register_service("snapshot_store", handlers["snapshot_store"])
        self._container.register_singleton(
            CONTAINER_KEY_TRANSACTION_UNIT_OF_WORK,
            handlers["transaction_unit_of_work"],
        )
        self._registry.register_service(
            "transaction_unit_of_work",
            handlers["transaction_unit_of_work"],
        )
        self._container.register_singleton(
            CONTAINER_KEY_METRICS_COLLECTOR,
            handlers["metrics_collector"],
        )
        self._registry.register_service(
            "metrics_collector",
            handlers["metrics_collector"],
        )
        self._container.register_singleton(
            CONTAINER_KEY_MODULE_REGISTRY,
            self._module_registry,
        )
        loader_manager = self._factory.create_loader_manager(
            self._module_registry,
            self._container,
        )
        self._container.register_singleton(
            CONTAINER_KEY_LOADER_MANAGER,
            loader_manager,
        )
        certified_plugin_registry = register_certified_plugin_registry(self._container)
        from core.plugins.registry.provider import set_default_registry_instance

        set_default_registry_instance(certified_plugin_registry)

        self._built = True
        return self

    def reset(self) -> None:
        """Clear container and registry state."""
        if self._built:
            shutdown_modules(self._container, self._module_registry)
        self._container.clear()
        self._registry.clear()
        self._module_registry = create_module_registry()
        self._factory = ApplicationFactory(self._configuration, self._container)
        self._built = False

    @property
    def is_built(self) -> bool:
        return self._built

    def container(self) -> Container:
        return self._container

    def registry(self) -> Registry:
        return self._registry

    def module_registry(self) -> ModuleRegistry:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_MODULE_REGISTRY)

    def loader_manager(self) -> LoaderManager:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_LOADER_MANAGER)

    def command_bus(self) -> CommandBus:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_COMMAND_BUS)

    def query_bus(self) -> QueryBus:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_QUERY_BUS)

    def unit_of_work(self) -> InMemoryUnitOfWork:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_UNIT_OF_WORK)

    def engine(self) -> StubEngine:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_ENGINE)

    def engine_lifecycle(self) -> EngineLifecycleManager:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_ENGINE_LIFECYCLE)

    def plugin_manager(self) -> PluginManager:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_PLUGIN_MANAGER)

    def provider_manager(self) -> ProviderManager:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_PROVIDER_MANAGER)

    def event_bus(self) -> InMemoryEventBus:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_EVENT_BUS)

    def published_event_store(self) -> PublishedEventStore:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_PUBLISHED_EVENT_STORE)

    def snapshot_store(self) -> InMemorySnapshotStore:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_SNAPSHOT_STORE)

    def transaction_unit_of_work(self) -> IUnitOfWork:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_TRANSACTION_UNIT_OF_WORK)

    def metrics_collector(self) -> InMemoryMetricsCollector:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_METRICS_COLLECTOR)

    def certified_plugin_registry(self) -> Any:
        self._ensure_built()
        return self._container.resolve(CONTAINER_KEY_CERTIFIED_PLUGIN_REGISTRY)

    def _ensure_built(self) -> None:
        if not self._built:
            msg = "Bootstrap.build() must be called before resolving components."
            raise ContainerError(msg)
