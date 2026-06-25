"""Application object factory."""

from __future__ import annotations

from typing import Any

from core.report.factory import create_exporter
from core.report.interfaces import IReportExporter
from core.application.analysis_pipeline import AnalysisPipeline
from core.application.capability_catalog import CapabilityCatalog
from core.application.command_bus import CommandBus
from core.application.report_builder import ReportBuilder
from core.application.commands import (
    AddExplanationTrace,
    AddReportSection,
    CompleteAnalysisSession,
    CompleteReport,
    CreateAnalysisSession,
    CreateReport,
    FailAnalysisSession,
    GenerateText,
    RunAnalysis,
    StartAnalysisSession,
)
from core.application.handlers import (
    AddExplanationTraceHandler,
    AddReportSectionHandler,
    CompleteAnalysisSessionHandler,
    CompleteReportHandler,
    CreateAnalysisSessionHandler,
    CreateReportHandler,
    FailAnalysisSessionHandler,
    GenerateTextCommandHandler,
    GetAnalysisSessionHandler,
    GetEventsByAggregateHandler,
    GetEventsByTypeHandler,
    GetReportHandler,
    ListCapabilitiesQueryHandler,
    ListProvidersQueryHandler,
    ListReportsHandler,
    RunAnalysisCommandHandler,
    StartAnalysisSessionHandler,
)
from core.application.queries import (
    GetAnalysisSession,
    GetEventsByAggregate,
    GetEventsByType,
    GetReport,
    ListCapabilities,
    ListProviders,
    ListReports,
)
from core.application.query_bus import QueryBus
from core.application.use_cases import (
    AddExplanationTraceUseCase,
    AddReportSectionUseCase,
    CompleteAnalysisSessionUseCase,
    CompleteReportUseCase,
    CreateAnalysisSessionUseCase,
    CreateReportUseCase,
    FailAnalysisSessionUseCase,
    GenerateTextUseCase,
    GetAnalysisSessionUseCase,
    GetEventsByAggregateUseCase,
    GetEventsByTypeUseCase,
    GetReportUseCase,
    ListCapabilitiesUseCase,
    ListProvidersUseCase,
    ListReportsUseCase,
    RunAnalysisUseCase,
    StartAnalysisSessionUseCase,
)
from core.bootstrap.configuration import EngineConfiguration
from core.container.container import Container
from core.container.interfaces import IContainer
from core.engine.adapter import EngineAdapter
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.stub_engine import StubEngine
from core.plugin.loader import PluginLoader
from core.plugin.manager import PluginManager
from core.plugin.registry import PluginRegistry
from core.plugin.analysis_stubs import (
    CareerStubPlugin,
    MasterLockStubPlugin,
    RelationshipStubPlugin,
    WealthStubPlugin,
)
from core.plugin.stub import StubPlugin
from core.provider.manager import ProviderManager
from core.provider.named_stubs import (
    ClaudeStubProvider,
    GeminiStubProvider,
    LocalModelStubProvider,
    OpenAIStubProvider,
)
from core.provider.registry import ProviderRegistry
from core.provider.stub import StubProvider
from core.infrastructure.memory_event_publisher import InMemoryEventPublisher
from core.infrastructure.memory_event_store import InMemoryEventStore as AggregateEventStore
from core.infrastructure.memory_repository import (
    InMemoryAnalysisSessionRepository,
    InMemoryReportRepository,
)
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork as AggregateUnitOfWork
from core.events.in_memory_bus import InMemoryEventBus
from core.events.interfaces import IEventBus
from core.events.replay import ReplayEngine
from core.events.recovery import AggregateRecovery
from core.events.store.in_memory_store import InMemoryEventStore
from core.events.store.interfaces import IEventStore
from core.events.snapshot.in_memory_store import InMemorySnapshotStore
from core.events.snapshot.interfaces import ISnapshotStore
from core.events.snapshot.sqlite_store import SQLiteSnapshotStore
from core.events.snapshot.policy import SnapshotPolicy
from core.events.store.sqlite_store import SQLiteEventStore
from core.events.wiring import wire_event_store, wire_snapshot_policy
from core.metrics.interfaces import IMetricsCollector
from core.metrics.in_memory import InMemoryMetricsCollector
from core.modules.loader.directory_loader import DirectoryModuleLoader
from core.modules.loader.manager import LoaderManager
from core.modules.loader.stubs import WhlModuleLoader, ZipModuleLoader
from core.modules.registry import ModuleRegistry
from core.uow.in_memory import InMemoryUnitOfWork as TransactionInMemoryUnitOfWork
from core.uow.interfaces import IUnitOfWork
from core.uow.sqlite import SQLiteUnitOfWork
from core.uow.transactional_stores import TransactionalEventStore, TransactionalSnapshotStore
from core.workflow.engine import WorkflowEngine
from core.workflow.report_builder import WorkflowReportBuilder


class ApplicationFactory:
    """Creates wired application and infrastructure components."""

    def __init__(
        self,
        configuration: EngineConfiguration | None = None,
        container: IContainer | None = None,
    ) -> None:
        self._configuration = configuration or EngineConfiguration.default()
        self._container = container or Container()

    def container(self) -> IContainer:
        """Return the dependency injection container."""
        return self._container

    @property
    def configuration(self) -> EngineConfiguration:
        return self._configuration

    def create_metrics_collector(self) -> IMetricsCollector:
        """Create an in-memory metrics collector."""
        return InMemoryMetricsCollector()

    def create_module_loader(self) -> DirectoryModuleLoader:
        """Create a directory-based dynamic module loader."""
        return DirectoryModuleLoader()

    def create_loader_manager(
        self,
        registry: ModuleRegistry,
        container: IContainer,
    ) -> LoaderManager:
        """Create a loader manager with registered package loaders."""
        manager = LoaderManager(registry, container)
        manager.register_loader(self.create_module_loader())
        manager.register_loader(ZipModuleLoader())
        manager.register_loader(WhlModuleLoader())
        return manager

    def create_aggregate_unit_of_work(self) -> AggregateUnitOfWork:
        """Create a fresh aggregate unit of work for domain persistence."""
        return AggregateUnitOfWork()

    def create_unit_of_work(
        self,
        event_store: IEventStore,
        snapshot_store: ISnapshotStore,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> IUnitOfWork:
        """Create a workflow transaction unit of work."""
        if self._configuration.event_storage == "sqlite":
            if not isinstance(event_store, SQLiteEventStore):
                msg = "SQLite unit of work requires SQLiteEventStore."
                raise TypeError(msg)
            if not isinstance(snapshot_store, SQLiteSnapshotStore):
                msg = "SQLite unit of work requires SQLiteSnapshotStore."
                raise TypeError(msg)
            return SQLiteUnitOfWork(
                self._configuration.sqlite_path,
                event_store,
                snapshot_store,
                event_bus,
                metrics_collector=metrics_collector,
            )
        return TransactionInMemoryUnitOfWork(
            event_store,
            snapshot_store,
            event_bus,
            metrics_collector=metrics_collector,
        )

    def create_repositories(
        self,
        unit_of_work: AggregateUnitOfWork,
    ) -> dict[str, Any]:
        """Expose repositories from the unit of work."""
        return {
            "analysis_session": unit_of_work.sessions,
            "report": unit_of_work.reports,
        }

    def create_aggregate_event_store(
        self,
        unit_of_work: AggregateUnitOfWork,
    ) -> AggregateEventStore:
        """Return the aggregate event store from the unit of work."""
        return unit_of_work.event_store

    def create_event_publisher(
        self,
        unit_of_work: AggregateUnitOfWork,
    ) -> InMemoryEventPublisher:
        """Return the event publisher from the unit of work."""
        return unit_of_work.event_publisher

    def create_handlers(
        self,
        unit_of_work: AggregateUnitOfWork,
        engine_adapter: EngineAdapter,
        plugin_manager: PluginManager,
        provider_manager: ProviderManager,
        event_bus: IEventBus | None = None,
        event_store: IEventStore | None = None,
        snapshot_store: ISnapshotStore | None = None,
    ) -> dict[str, Any]:
        """Create command and query handlers backed by use cases."""
        store: IEventStore = event_store or self.create_event_store()
        snapshots: ISnapshotStore = snapshot_store or self.create_snapshot_store()
        if self._configuration.event_storage == "inmemory":
            if not isinstance(store, TransactionalEventStore):
                store = TransactionalEventStore(store)
            if not isinstance(snapshots, TransactionalSnapshotStore):
                snapshots = TransactionalSnapshotStore(snapshots)
        policy = self.create_snapshot_policy()
        bus = event_bus or self.create_event_bus()
        metrics = self.create_metrics_collector()
        wire_event_store(bus, store)
        wire_snapshot_policy(bus, store, snapshots, policy)
        transaction_uow = self.create_unit_of_work(store, snapshots, bus, metrics)
        use_cases = self._create_use_cases(
            unit_of_work,
            engine_adapter,
            plugin_manager,
            provider_manager,
            bus,
            metrics,
        )
        command_handlers = {
            CreateAnalysisSession: CreateAnalysisSessionHandler(
                use_cases["create_analysis_session"],
            ),
            StartAnalysisSession: StartAnalysisSessionHandler(
                use_cases["start_analysis_session"],
            ),
            CompleteAnalysisSession: CompleteAnalysisSessionHandler(
                use_cases["complete_analysis_session"],
            ),
            FailAnalysisSession: FailAnalysisSessionHandler(
                use_cases["fail_analysis_session"],
            ),
            CreateReport: CreateReportHandler(use_cases["create_report"]),
            AddReportSection: AddReportSectionHandler(use_cases["add_report_section"]),
            AddExplanationTrace: AddExplanationTraceHandler(
                use_cases["add_explanation_trace"],
            ),
            CompleteReport: CompleteReportHandler(use_cases["complete_report"]),
            RunAnalysis: RunAnalysisCommandHandler(use_cases["run_analysis"]),
            GenerateText: GenerateTextCommandHandler(use_cases["generate_text"]),
        }
        query_handlers = {
            GetAnalysisSession: GetAnalysisSessionHandler(
                use_cases["get_analysis_session"],
            ),
            GetReport: GetReportHandler(use_cases["get_report"]),
            ListReports: ListReportsHandler(use_cases["list_reports"]),
            ListCapabilities: ListCapabilitiesQueryHandler(
                use_cases["list_capabilities"],
            ),
            ListProviders: ListProvidersQueryHandler(
                use_cases["list_providers"],
            ),
            GetEventsByAggregate: GetEventsByAggregateHandler(
                use_cases["get_events_by_aggregate"],
            ),
            GetEventsByType: GetEventsByTypeHandler(use_cases["get_events_by_type"]),
        }
        return {
            "use_cases": use_cases,
            "command_handlers": command_handlers,
            "query_handlers": query_handlers,
            "event_bus": bus,
            "event_store": store,
            "snapshot_store": snapshots,
            "snapshot_policy": policy,
            "transaction_unit_of_work": transaction_uow,
            "metrics_collector": metrics,
        }

    def create_command_bus(self, command_handlers: dict[type[Any], Any]) -> CommandBus:
        """Create a command bus with handlers registered."""
        bus = CommandBus()
        for command_type, handler in command_handlers.items():
            bus.register(command_type, handler)
        return bus

    def create_query_bus(self, query_handlers: dict[type[Any], Any]) -> QueryBus:
        """Create a query bus with handlers registered."""
        bus = QueryBus()
        for query_type, handler in query_handlers.items():
            bus.register(query_type, handler)
        return bus

    def create_event_bus(self) -> InMemoryEventBus:
        """Create a synchronous in-memory event bus."""
        return InMemoryEventBus()

    def create_event_store(self) -> IEventStore:
        """Create a published event store based on configuration."""
        if self._configuration.event_storage == "sqlite":
            return self.create_sqlite_event_store()
        return InMemoryEventStore()

    def create_sqlite_event_store(self, db_path: str | None = None) -> SQLiteEventStore:
        """Create a SQLite-backed published event store."""
        path = db_path or self._configuration.sqlite_path
        return SQLiteEventStore(path)

    def create_snapshot_store(self) -> ISnapshotStore:
        """Create a snapshot store based on configuration."""
        if self._configuration.event_storage == "sqlite":
            return self.create_sqlite_snapshot_store()
        return InMemorySnapshotStore()

    def create_sqlite_snapshot_store(self, db_path: str | None = None) -> SQLiteSnapshotStore:
        """Create a SQLite-backed snapshot store."""
        path = db_path or self._configuration.sqlite_path
        return SQLiteSnapshotStore(path)

    def create_snapshot_policy(self, every_n_events: int = 50) -> SnapshotPolicy:
        """Create a snapshot creation policy."""
        return SnapshotPolicy(every_n_events=every_n_events)

    def create_replay_engine(
        self,
        snapshot_store: ISnapshotStore | None = None,
    ) -> ReplayEngine:
        """Create an event replay engine."""
        return ReplayEngine(snapshot_store)

    def create_aggregate_recovery(
        self,
        event_store: IEventStore,
        snapshot_store: ISnapshotStore,
        replay_engine: ReplayEngine | None = None,
        policy: SnapshotPolicy | None = None,
    ) -> AggregateRecovery:
        """Create an aggregate recovery service."""
        return AggregateRecovery(
            event_store,
            snapshot_store,
            replay_engine or self.create_replay_engine(snapshot_store),
            policy or self.create_snapshot_policy(),
        )

    def create_report_builder(
        self,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> ReportBuilder:
        """Create a report builder for canonical rendering."""
        return ReportBuilder(event_bus=event_bus, metrics_collector=metrics_collector)

    def create_report_exporter(
        self,
        export_format: str,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> IReportExporter:
        """Create a report exporter for the requested format."""
        return create_exporter(
            export_format,
            event_bus=event_bus,
            metrics_collector=metrics_collector,
        )

    def create_workflow_engine(
        self,
        run_analysis_use_case: RunAnalysisUseCase,
        event_bus: IEventBus | None = None,
        unit_of_work: IUnitOfWork | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> WorkflowEngine:
        """Create a workflow engine backed by RunAnalysisUseCase."""
        return WorkflowEngine(
            run_analysis_use_case,
            event_bus,
            unit_of_work,
            metrics_collector,
        )

    def create_workflow_builder(
        self,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> WorkflowReportBuilder:
        """Create a workflow report builder."""
        return WorkflowReportBuilder(
            report_builder=self.create_report_builder(event_bus, metrics_collector),
        )

    def create_analysis_pipeline(
        self,
        plugin_manager: PluginManager,
        provider_manager: ProviderManager | None = None,
    ) -> AnalysisPipeline:
        """Create the XAI-enabled analysis pipeline."""
        return AnalysisPipeline(plugin_manager, provider_manager)

    def create_capability_catalog(
        self,
        plugin_manager: PluginManager,
    ) -> CapabilityCatalog:
        """Create a capability catalog for RunAnalysis validation."""
        supported = (
            frozenset(self._configuration.supported_capabilities)
            if self._configuration.supported_capabilities is not None
            else None
        )
        return CapabilityCatalog(plugin_manager, supported)

    def create_engine(
        self,
        unit_of_work: AggregateUnitOfWork,
        plugin_manager: PluginManager | None = None,
    ) -> StubEngine:
        """Create a stub engine wired to the unit of work."""
        engine = StubEngine(
            unit_of_work,
            self._configuration,
            plugin_manager,
        )
        engine.initialize()
        return engine

    def create_engine_lifecycle_manager(
        self,
        engine: StubEngine,
    ) -> EngineLifecycleManager:
        """Create a lifecycle manager for the engine."""
        return EngineLifecycleManager(engine)

    def create_engine_adapter(
        self,
        engine: StubEngine,
        lifecycle_manager: EngineLifecycleManager,
    ) -> EngineAdapter:
        """Create an adapter wrapping the engine kernel."""
        return EngineAdapter(engine, lifecycle_manager)

    def create_plugin_registry(self) -> PluginRegistry:
        """Create an empty plugin registry."""
        return PluginRegistry()

    def create_plugin_loader(self, registry: PluginRegistry) -> PluginLoader:
        """Create a plugin loader bound to a registry."""
        return PluginLoader(registry)

    def create_plugin_manager(self, registry: PluginRegistry) -> PluginManager:
        """Create a plugin manager bound to a registry."""
        return PluginManager(registry)

    def create_analysis_stub_plugins(self) -> list[Any]:
        """Create default analysis stub plugins for bootstrap registration."""
        return [
            StubPlugin(),
            MasterLockStubPlugin(),
            WealthStubPlugin(),
            CareerStubPlugin(),
            RelationshipStubPlugin(),
        ]

    def create_provider_registry(self) -> ProviderRegistry:
        """Create an empty provider registry."""
        return ProviderRegistry()

    def create_provider_manager(self, registry: ProviderRegistry) -> ProviderManager:
        """Create a provider manager bound to a registry."""
        return ProviderManager(registry)

    def create_default_providers(self) -> list[Any]:
        """Create default provider stubs for bootstrap registration."""
        return [
            StubProvider(),
            OpenAIStubProvider(),
            ClaudeStubProvider(),
            GeminiStubProvider(),
            LocalModelStubProvider(),
        ]

    def _create_use_cases(
        self,
        unit_of_work: AggregateUnitOfWork,
        engine_adapter: EngineAdapter,
        plugin_manager: PluginManager,
        provider_manager: ProviderManager,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> dict[str, Any]:
        return {
            "create_analysis_session": CreateAnalysisSessionUseCase(unit_of_work),
            "start_analysis_session": StartAnalysisSessionUseCase(unit_of_work),
            "complete_analysis_session": CompleteAnalysisSessionUseCase(unit_of_work),
            "fail_analysis_session": FailAnalysisSessionUseCase(unit_of_work),
            "create_report": CreateReportUseCase(unit_of_work),
            "add_report_section": AddReportSectionUseCase(unit_of_work),
            "add_explanation_trace": AddExplanationTraceUseCase(unit_of_work),
            "complete_report": CompleteReportUseCase(unit_of_work),
            "run_analysis": RunAnalysisUseCase(
                engine_adapter,
                plugin_manager,
                provider_manager,
                self.create_capability_catalog(plugin_manager),
                self.create_analysis_pipeline(plugin_manager, provider_manager),
                event_bus,
                metrics_collector,
            ),
            "generate_text": GenerateTextUseCase(provider_manager),
            "get_analysis_session": GetAnalysisSessionUseCase(unit_of_work),
            "get_report": GetReportUseCase(unit_of_work),
            "list_reports": ListReportsUseCase(unit_of_work),
            "get_events_by_aggregate": GetEventsByAggregateUseCase(unit_of_work),
            "get_events_by_type": GetEventsByTypeUseCase(unit_of_work),
            "list_capabilities": ListCapabilitiesUseCase(plugin_manager),
            "list_providers": ListProvidersUseCase(provider_manager),
        }


def create_certified_plugin_registry() -> Any:
    """Create a certified plugin registry backed by the default JSON store."""
    from core.plugins.registry.audit import get_default_audit_logger
    from core.plugins.registry.certified import CertifiedPluginRegistry
    from core.plugins.registry.json_store import JsonCertifiedPluginRegistryStore
    from core.plugins.registry.paths import (
        ensure_default_registry_directory,
        ensure_default_registry_file,
    )

    ensure_default_registry_directory()
    registry_path = ensure_default_registry_file()
    store = JsonCertifiedPluginRegistryStore(registry_path)
    return CertifiedPluginRegistry(store=store, audit_logger=get_default_audit_logger())


def register_certified_plugin_registry(container: Any) -> Any:
    """Register the certified plugin registry singleton in the DI container."""
    key = "certified_plugin_registry"
    if container.exists(key):
        return container.resolve(key)
    registry = create_certified_plugin_registry()
    container.register_singleton(key, registry)
    return registry
