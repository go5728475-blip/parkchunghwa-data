"""Development CLI entry point for MASTER ENGINE."""

from __future__ import annotations

import sys
from uuid import uuid4

from core.application.commands import GenerateText, RunAnalysis
from core.application.queries import ListCapabilities, ListProviders
from core.application.result import Failure, Success
from core.report.errors import UnsupportedExportFormat
from core.report.factory import create_exporter
from core.events.in_memory_bus import InMemoryEventBus
from core.events.snapshot.sqlite_store import SQLiteSnapshotStore
from core.events.store.sqlite_store import SQLiteEventStore
from core.bootstrap.factory import ApplicationFactory
from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.configuration import EngineConfiguration
from core.common.error_codes import ErrorCode
from core.contracts.metadata import Metadata
from core.domain.built_report import BuiltReport
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.engine.response import EngineRunResponse
from core.domain.value_objects import BirthData, EngineContext
from core.workflow.models import ExecutionMode, Workflow, WorkflowResult, WorkflowRunContext


def _metadata() -> Metadata:
    return Metadata(correlation_id=uuid4())


_DEFAULT_WORKFLOW_CAPABILITIES = (
    "wealth.analysis",
    "career.analysis",
    "relationship.analysis",
)


def _parse_run_workflow_options(
    args: list[str],
) -> tuple[tuple[str, ...], str | None, str | None]:
    capabilities: list[str] = []
    provider_id: str | None = None
    export_format: str | None = None
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--capability" and index + 1 < len(args):
            capabilities.append(args[index + 1])
            index += 2
            continue
        if token == "--provider-id" and index + 1 < len(args):
            provider_id = args[index + 1]
            index += 2
            continue
        if token == "--format" and index + 1 < len(args):
            export_format = args[index + 1]
            index += 2
            continue
        index += 1
    if not capabilities:
        capabilities = list(_DEFAULT_WORKFLOW_CAPABILITIES)
    return tuple(capabilities), provider_id, export_format


def _parse_export_report_options(args: list[str]) -> tuple[str, str, str | None]:
    export_format = "json"
    capability = "stub.analysis"
    provider_id: str | None = None
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--format" and index + 1 < len(args):
            export_format = args[index + 1]
            index += 2
            continue
        if token == "--capability" and index + 1 < len(args):
            capability = args[index + 1]
            index += 2
            continue
        if token == "--provider-id" and index + 1 < len(args):
            provider_id = args[index + 1]
            index += 2
            continue
        index += 1
    return export_format, capability, provider_id


def _parse_run_analysis_options(args: list[str]) -> tuple[str, str | None]:
    capability = "stub.analysis"
    provider_id: str | None = None
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--capability" and index + 1 < len(args):
            capability = args[index + 1]
            index += 2
            continue
        if token == "--provider-id" and index + 1 < len(args):
            provider_id = args[index + 1]
            index += 2
            continue
        index += 1
    return capability, provider_id


def _failure_suggestion(code: str) -> str | None:
    if code == ErrorCode.PROVIDER_NOT_FOUND:
        return "python -m core.cli.main list-providers"
    if code in (
        ErrorCode.CAPABILITY_NOT_FOUND,
        ErrorCode.CAPABILITY_DISABLED,
        ErrorCode.CAPABILITY_NOT_SUPPORTED,
    ):
        return "python -m core.cli.main list-capabilities"
    if code == ErrorCode.PROVIDER_DISABLED:
        return "choose an enabled provider from list-providers"
    return None


def _print_failure(command_name: str, error: object) -> None:
    code = getattr(error, "code", "UNKNOWN_ERROR")
    message = getattr(error, "message", str(error))
    print(f"[MASTER ENGINE] {command_name} failed")
    print(f"  code:    {code}")
    print(f"  message: {message}")
    suggestion = _failure_suggestion(code)
    if suggestion:
        print(f"  suggestion: {suggestion}")


def _print_xai_details(response: EngineRunResponse) -> None:
    if response.analysis_result is None:
        print("[MASTER ENGINE] No analysis result available.")
        return

    for section in response.analysis_result.sections:
        print(f"Section: [{section.source}] {section.title}")
        print(section.content)
        print(f"Confidence: {section.explanation.confidence}")
        print("Reasoning:")
        for step in section.explanation.reasoning:
            print(f"  - {step}")
        print("Evidence:")
        for item in section.explanation.evidence:
            print(f"  - {item}")
        if section.enriched_from_section_id is not None:
            print(f"Enriched from: {section.enriched_from_section_id}")
        print()

    if response.analysis_result.trace:
        print("Trace:")
        for entry in response.analysis_result.trace:
            print(f"  {entry.step} | {entry.source} | {entry.timestamp}")
            print(f"    {entry.message}")


def run_dev_analysis() -> int:
    """Build the engine graph, dispatch RunAnalysis, and print the result."""
    return run_analysis()


def run_analysis(
    capability: str = "stub.analysis",
    provider_id: str | None = None,
) -> int:
    """Dispatch RunAnalysis with optional capability and provider routing."""
    if provider_id is not None and not provider_id.strip():
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print("  message: Provider id cannot be blank.")
        return 1

    bootstrap = Bootstrap().build()
    command_bus = bootstrap.command_bus()

    user_id = UserId.new()
    session_id = SessionId.new()
    try:
        command = RunAnalysis(
            metadata=_metadata(),
            session_id=session_id,
            user_id=user_id,
            birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
            context=EngineContext(user_id=user_id, session_id=session_id),
            capability=capability,
            provider_id=ProviderId(value=provider_id) if provider_id else None,
        )
    except ValueError as exc:
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print(f"  message: {exc}")
        return 1

    result = command_bus.dispatch(command)
    if isinstance(result, Failure):
        _print_failure("RunAnalysis", result.unwrap_error())
        return 1

    response = result.unwrap()
    report = bootstrap.unit_of_work().reports.get(response.report_id)
    print("[MASTER ENGINE] RunAnalysis completed")
    print(f"  session_id:  {response.session_id}")
    print(f"  report_id:   {response.report_id}")
    print(f"  status:      {response.status}")
    print(f"  capability:  {capability}")
    if provider_id:
        print(f"  provider_id: {provider_id}")
    if response.analysis_result is not None:
        for section in response.analysis_result.sections:
            print(f"[{section.source}]")
            print(section.content)
            print()
        if response.analysis_result.trace:
            print("trace:")
            for entry in response.analysis_result.trace:
                print(f"  {entry.step}:{entry.source}")
    elif report is not None and report.sections:
        print(f"  section:     {report.sections[0].content}")
    return 0


def explain_analysis(
    capability: str = "wealth.analysis",
    provider_id: str | None = "openai.stub",
) -> int:
    """Run analysis and print explainable AI details."""
    if provider_id is not None and not provider_id.strip():
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print("  message: Provider id cannot be blank.")
        return 1

    bootstrap = Bootstrap().build()
    command_bus = bootstrap.command_bus()

    user_id = UserId.new()
    session_id = SessionId.new()
    try:
        command = RunAnalysis(
            metadata=_metadata(),
            session_id=session_id,
            user_id=user_id,
            birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
            context=EngineContext(user_id=user_id, session_id=session_id),
            capability=capability,
            provider_id=ProviderId(value=provider_id) if provider_id else None,
        )
    except ValueError as exc:
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print(f"  message: {exc}")
        return 1

    result = command_bus.dispatch(command)
    if isinstance(result, Failure):
        _print_failure("RunAnalysis", result.unwrap_error())
        return 1

    response = result.unwrap()
    print("[MASTER ENGINE] Explainable Analysis")
    print(f"  capability:  {capability}")
    if provider_id:
        print(f"  provider_id: {provider_id}")
    print()
    _print_xai_details(response)
    return 0


def _print_rendered_report(built_report: BuiltReport) -> None:
    print(f"Title: {built_report.title}")
    print()
    print("Summary:")
    print(built_report.summary)
    print()
    print("TOC:")
    for entry in built_report.toc:
        print(f"  {entry.order}. {entry.title}")
    print()
    for group in built_report.capability_groups:
        print(f"[{group.label}]")
        for section in group.sections:
            print(section.title)
            print(section.content)
            print(f"Confidence: {section.confidence.value}")
            if section.reasoning:
                print("Reasoning:")
                for step in section.reasoning:
                    print(f"  - {step}")
            if section.evidence:
                print("Evidence:")
                for item in section.evidence:
                    print(f"  - {item}")
            print()
    if built_report.trace:
        print("Trace:")
        for entry in built_report.trace:
            print(f"  {entry.step} | {entry.source} | {entry.timestamp}")
            print(f"    {entry.message}")


def render_report(
    capability: str = "stub.analysis",
    provider_id: str | None = None,
) -> int:
    """Run analysis and render a canonical built report."""
    if provider_id is not None and not provider_id.strip():
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print("  message: Provider id cannot be blank.")
        return 1

    bootstrap = Bootstrap().build()
    command_bus = bootstrap.command_bus()
    factory = ApplicationFactory()
    metrics = bootstrap.metrics_collector()
    builder = factory.create_report_builder(bootstrap.event_bus(), metrics)

    user_id = UserId.new()
    session_id = SessionId.new()
    try:
        command = RunAnalysis(
            metadata=_metadata(),
            session_id=session_id,
            user_id=user_id,
            birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
            context=EngineContext(user_id=user_id, session_id=session_id),
            capability=capability,
            provider_id=ProviderId(value=provider_id) if provider_id else None,
        )
    except ValueError as exc:
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print(f"  message: {exc}")
        return 1

    result = command_bus.dispatch(command)
    if isinstance(result, Failure):
        _print_failure("RunAnalysis", result.unwrap_error())
        return 1

    response = result.unwrap()
    if response.analysis_result is None:
        print("[MASTER ENGINE] No analysis result available for rendering.")
        return 1

    built_report = builder.build(response.analysis_result)
    print("[MASTER ENGINE] Rendered Report")
    print(f"  report_id: {built_report.report_id}")
    print()
    _print_rendered_report(built_report)
    return 0


def export_report(
    export_format: str = "json",
    capability: str = "stub.analysis",
    provider_id: str | None = None,
) -> int:
    """Run analysis, build a report, and export it to stdout."""
    if provider_id is not None and not provider_id.strip():
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print("  message: Provider id cannot be blank.")
        return 1

    bootstrap = Bootstrap().build()
    metrics = bootstrap.metrics_collector()

    try:
        exporter = create_exporter(
            export_format,
            event_bus=bootstrap.event_bus(),
            metrics_collector=metrics,
        )
    except UnsupportedExportFormat as exc:
        print("[MASTER ENGINE] ExportReport failed")
        print(f"  message: {exc}")
        return 1

    command_bus = bootstrap.command_bus()
    factory = ApplicationFactory()
    builder = factory.create_report_builder(bootstrap.event_bus(), metrics)

    user_id = UserId.new()
    session_id = SessionId.new()
    try:
        command = RunAnalysis(
            metadata=_metadata(),
            session_id=session_id,
            user_id=user_id,
            birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
            context=EngineContext(user_id=user_id, session_id=session_id),
            capability=capability,
            provider_id=ProviderId(value=provider_id) if provider_id else None,
        )
    except ValueError as exc:
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print(f"  message: {exc}")
        return 1

    result = command_bus.dispatch(command)
    if isinstance(result, Failure):
        _print_failure("RunAnalysis", result.unwrap_error())
        return 1

    response = result.unwrap()
    if response.analysis_result is None:
        print("[MASTER ENGINE] No analysis result available for export.")
        return 1

    built_report = builder.build(response.analysis_result)
    print(exporter.export(built_report), end="")
    return 0


def _print_workflow_summary(
    workflow: Workflow,
    workflow_result: WorkflowResult,
    built_report: BuiltReport,
) -> None:
    print("[MASTER ENGINE] Workflow Summary")
    print(f"  workflow_id: {workflow.workflow_id}")
    print(f"  name:        {workflow.name}")
    print(f"  mode:        {workflow.execution_mode.value}")
    print(f"  capabilities: {', '.join(workflow.capabilities)}")
    print()
    print("Capability Results:")
    for capability, analysis_result in zip(
        workflow.capabilities,
        workflow_result.analysis_results,
        strict=True,
    ):
        print(f"  [{capability}]")
        for section in analysis_result.sections:
            print(f"    {section.title}: {section.content}")
    print()
    print("Report Summary:")
    print(built_report.summary)
    print()
    if workflow_result.trace:
        print("Trace:")
        for entry in workflow_result.trace:
            print(f"  {entry.step.value} | {entry.source} | {entry.timestamp}")
            print(f"    {entry.message}")


def run_workflow(
    capabilities: tuple[str, ...] | None = None,
    provider_id: str | None = None,
    export_format: str | None = None,
) -> int:
    """Run a multi-capability workflow and render or export the unified report."""
    if provider_id is not None and not provider_id.strip():
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print("  message: Provider id cannot be blank.")
        return 1

    workflow_capabilities = capabilities or _DEFAULT_WORKFLOW_CAPABILITIES
    bootstrap = Bootstrap().build()
    factory = ApplicationFactory()
    event_bus = bootstrap.event_bus()
    metrics = bootstrap.metrics_collector()
    run_analysis = bootstrap.registry().get_use_case("run_analysis")
    transaction_uow = bootstrap.transaction_unit_of_work()
    workflow_engine = factory.create_workflow_engine(
        run_analysis,
        event_bus,
        transaction_uow,
        metrics,
    )
    workflow_builder = factory.create_workflow_builder(event_bus, metrics)

    user_id = UserId.new()
    session_id = SessionId.new()
    workflow = Workflow(
        workflow_id=WorkflowId.new(),
        name="MASTER ENGINE Workflow",
        capabilities=workflow_capabilities,
        execution_mode=ExecutionMode.SEQUENTIAL,
    )
    context = WorkflowRunContext(
        metadata=_metadata(),
        session_id=session_id,
        user_id=user_id,
        birth_data=BirthData(year=1990, month=1, day=1, hour=12, minute=0),
    )

    try:
        provider = ProviderId(value=provider_id) if provider_id else None
    except ValueError as exc:
        print("[MASTER ENGINE] RunAnalysis validation failed")
        print(f"  message: {exc}")
        return 1

    result = workflow_engine.run(workflow, context, provider_id=provider)
    if isinstance(result, Failure):
        _print_failure("RunWorkflow", result.unwrap_error())
        return 1

    workflow_result = result.unwrap()
    built_report = workflow_builder.build(workflow, workflow_result)

    if export_format is not None:
        try:
            exporter = create_exporter(
                export_format,
                event_bus=event_bus,
                metrics_collector=metrics,
            )
        except UnsupportedExportFormat as exc:
            print("[MASTER ENGINE] ExportReport failed")
            print(f"  message: {exc}")
            return 1
        print(exporter.export(built_report), end="")
        return 0

    _print_workflow_summary(workflow, workflow_result, built_report)
    return 0


def show_events(event_bus: InMemoryEventBus | None = None) -> int:
    """Print recent domain events from the event bus."""
    bus = event_bus
    if bus is None:
        bootstrap = Bootstrap().build()
        bus = bootstrap.event_bus()

    print("[MASTER ENGINE] Recent Domain Events")
    events = bus.recent_events()
    if not events:
        print("  (no events)")
        return 0

    for event in events:
        print(f"  {event.event_type} | {event.occurred_at} | {event.aggregate_id}")
    return 0


def _parse_replay_events_options(args: list[str]) -> str | None:
    aggregate_id: str | None = None
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--aggregate" and index + 1 < len(args):
            aggregate_id = args[index + 1]
            index += 2
            continue
        index += 1
    return aggregate_id


def replay_events(
    aggregate_id: str | None = None,
    event_store: object | None = None,
    snapshot_store: object | None = None,
) -> int:
    """Replay stored domain events and print a replay trace."""
    bootstrap = Bootstrap().build()
    store = event_store or bootstrap.published_event_store()
    snapshots = snapshot_store or bootstrap.snapshot_store()
    factory = ApplicationFactory()
    replay_engine = factory.create_replay_engine(snapshots)

    if aggregate_id is not None:
        events = store.list_by_aggregate(aggregate_id)
    else:
        events = store.list()

    print("[MASTER ENGINE] Replay Summary")
    if not events:
        print("  event count: 0")
        print("  (no stored events to replay)")
        return 0

    if aggregate_id is not None:
        result = replay_engine.replay_for_aggregate(aggregate_id, events, snapshots)
    else:
        result = replay_engine.replay(events)

    print(f"  replay_id:     {result.replay_id}")
    print(f"  event count:   {result.total_events}")
    print(f"  snapshot:      {'yes' if result.snapshot_applied else 'no'}")
    print(f"  start_pos:     {result.replay_start_position}")
    print(f"  started_at:    {result.started_at}")
    print(f"  finished_at:   {result.finished_at}")
    print()
    print("Replay Trace:")
    for entry in result.trace:
        print(
            f"  {entry.order}. {entry.event_type} | "
            f"{entry.occurred_at} | {entry.aggregate_id}",
        )
        print(f"     {entry.message}")
    return 0


def snapshot_status(
    event_store: object | None = None,
    snapshot_store: object | None = None,
) -> int:
    """Print snapshot status for stored aggregates."""
    bootstrap = Bootstrap().build()
    store = event_store or bootstrap.published_event_store()
    snapshots = snapshot_store or bootstrap.snapshot_store()

    aggregate_ids = sorted(
        {
            event.aggregate_id
            for event in store.list()
            if event.aggregate_id
        },
    )

    print("[MASTER ENGINE] Snapshot Status")
    if not aggregate_ids:
        print("  (no aggregates)")
        return 0

    for aggregate_id in aggregate_ids:
        snapshot = snapshots.get_latest(aggregate_id)
        print(f"  Aggregate: {aggregate_id}")
        if snapshot is None:
            print("    Latest Snapshot: (none)")
            print("    Version:         0")
            print("    CreatedAt:       -")
            print("    Replay Start:    0")
            continue
        print(f"    Latest Snapshot: {snapshot.snapshot_id}")
        print(f"    Version:         {snapshot.aggregate_version}")
        print(f"    CreatedAt:       {snapshot.created_at}")
        print(f"    Replay Start:    {snapshot.aggregate_version}")
    return 0


def event_store_info(configuration: EngineConfiguration | None = None) -> int:
    """Print published event and snapshot storage information."""
    config = configuration or EngineConfiguration.default()
    bootstrap = Bootstrap(config).build()
    store = bootstrap.published_event_store()
    snapshots = bootstrap.snapshot_store()

    db_path = config.sqlite_path if config.event_storage == "sqlite" else "-"
    if isinstance(store, SQLiteEventStore):
        db_path = store.db_path
    elif isinstance(snapshots, SQLiteSnapshotStore):
        db_path = snapshots.db_path

    print("[MASTER ENGINE] Event Store Info")
    print(f"  Storage Type:   {config.event_storage}")
    print(f"  Event Count:    {len(store.list())}")
    print(f"  Snapshot Count: {len(snapshots.list())}")
    print(f"  Database Path:  {db_path}")
    return 0


def transaction_status(
    unit_of_work: object | None = None,
) -> int:
    """Print the latest workflow transaction status."""
    bootstrap = Bootstrap().build()
    uow = unit_of_work or bootstrap.transaction_unit_of_work()
    context = uow.context

    print("[MASTER ENGINE] Transaction Status")
    print(f"  Active:      {context.active}")
    print(f"  Committed:   {context.committed}")
    print(f"  RolledBack:  {context.rolled_back}")
    print(f"  StartedAt:   {context.started_at or '-'}")
    print(f"  FinishedAt:  {context.finished_at or '-'}")
    return 0


def show_metrics(
    metrics_collector: object | None = None,
) -> int:
    """Print collected operational metrics."""
    bootstrap = Bootstrap().build()
    collector = metrics_collector or bootstrap.metrics_collector()
    metrics = collector.list()

    print("[MASTER ENGINE] Metrics")
    if not metrics:
        print("  (no metrics)")
        return 0

    print(f"  {'Metric':<28} {'Count':>7} {'Average':>12} {'Min':>12} {'Max':>12}")
    for metric in metrics:
        minimum = "-" if metric.min is None else f"{metric.min:.2f}"
        maximum = "-" if metric.max is None else f"{metric.max:.2f}"
        print(
            f"  {metric.metric_name:<28} {metric.count:>7} "
            f"{metric.avg:>12.2f} {minimum:>12} {maximum:>12}",
        )
    return 0


def list_modules(
    module_registry: object | None = None,
    certified_registry: object | None = None,
) -> int:
    """List registered engine modules."""
    from core.plugins.registry.resolver import module_certification_display, resolve_certified_registry

    bootstrap = Bootstrap().build()
    registry = module_registry or bootstrap.module_registry()
    certified = certified_registry or resolve_certified_registry(bootstrap.container())

    print("[MASTER ENGINE] Registered Modules")
    descriptors = registry.descriptors()
    if not descriptors:
        print("  (no modules)")
        return 0

    for descriptor in descriptors:
        loaded = "yes" if descriptor.loaded else "no"
        capabilities = ", ".join(descriptor.capabilities)
        certified_status, compatibility = module_certification_display(
            certified,
            descriptor.name,
        )
        print(
            f"  {descriptor.name} | v{descriptor.version} | "
            f"{capabilities} | loaded={loaded} | certified={certified_status} | "
            f"compatibility={compatibility}",
        )
    return 0


def module_info(
    module_name: str,
    module_registry: object | None = None,
    certified_registry: object | None = None,
) -> int:
    """Print details for a single engine module."""
    from core.plugins.registry.resolver import module_certification_display, resolve_certified_registry

    bootstrap = Bootstrap().build()
    registry = module_registry or bootstrap.module_registry()
    certified = certified_registry or resolve_certified_registry(bootstrap.container())

    if not registry.exists(module_name):
        print(f"[MASTER ENGINE] Module not found: {module_name}")
        return 1

    descriptor = registry.descriptor(module_name)
    certified_status, compatibility = module_certification_display(certified, descriptor.name)
    print("[MASTER ENGINE] Module Info")
    print(f"  Module Name: {descriptor.name}")
    print(f"  Version:     {descriptor.version}")
    print(f"  Capabilities: {', '.join(descriptor.capabilities)}")
    print(f"  Loaded:      {'yes' if descriptor.loaded else 'no'}")
    print(f"  Certified:   {certified_status}")
    print(f"  Compatibility: {compatibility}")
    return 0


def load_module(
    path: str,
    loader_manager: object | None = None,
    *,
    certified_only: bool = False,
    certification_gate: object | None = None,
    certified_registry: object | None = None,
    registry_path: str | None = None,
    require_registered: bool = False,
) -> int:
    """Load a dynamic module package from disk."""
    if require_registered and not certified_only:
        print("[MASTER ENGINE] LoadModule failed")
        print("  message: --require-registered requires --certified-only")
        return 1

    bootstrap = Bootstrap().build()
    manager = loader_manager or bootstrap.loader_manager()
    certification_record = None
    resolved_registry_path: str | None = None

    if certified_only:
        from core.plugins.certification.gate import CertificationGate
        from core.plugins.certification.load_gate import (
            PluginCertificationError,
        )
        from core.plugins.certification.loading import CertificationLoadError
        from core.runtime.load_pipeline import RuntimeLoadError, enforce_runtime_before_load

        registry = _resolve_certified_registry(
            bootstrap,
            certified_registry=certified_registry,
            registry_path=registry_path,
        )
        resolved_registry_path = _resolve_registry_path(registry_path)
        gate = certification_gate or CertificationGate(registry=registry)

        try:
            runtime_decision, certification_record, plugin, certification_loader = (
                enforce_runtime_before_load(
                    path,
                    certification_gate=gate,
                    certified_only=True,
                    certified_registry=registry,
                    require_registered=require_registered,
                    container=bootstrap.container(),
                )
            )
        except (CertificationLoadError, PluginCertificationError, RuntimeLoadError) as exc:
            print("[MASTER ENGINE] LoadModule failed")
            print(f"  message: {exc}")
            return 1
        finally:
            if "certification_loader" in locals() and certification_loader is not None:
                certification_loader.unload(plugin.name())

    try:
        module_name = manager.load(path)
    except Exception as exc:  # noqa: BLE001
        print("[MASTER ENGINE] LoadModule failed")
        print(f"  message: {exc}")
        return 1

    print("[MASTER ENGINE] Module Loaded")
    print(f"  Module Name: {module_name}")
    print(f"  Path:        {path}")
    if certification_record is not None:
        print(f"  Certified:           {certification_record.certified}")
        print(
            "  Compatibility Level: "
            f"{certification_record.compatibility_level.value}",
        )
        print(f"  Registered Required: {require_registered}")
        print(f"  Registry Path:       {resolved_registry_path}")
    if certified_only and "runtime_decision" in locals() and runtime_decision is not None:
        print(f"  Runtime Status:        {runtime_decision.decision.status.value}")
        if runtime_decision.warnings:
            print(f"  Runtime Warnings:      {', '.join(runtime_decision.warnings)}")
    return 0


def unload_module(
    module_name: str,
    loader_manager: object | None = None,
) -> int:
    """Unload a dynamic module package."""
    bootstrap = Bootstrap().build()
    manager = loader_manager or bootstrap.loader_manager()
    try:
        manager.unload(module_name)
    except Exception as exc:  # noqa: BLE001
        print("[MASTER ENGINE] UnloadModule failed")
        print(f"  message: {exc}")
        return 1

    print("[MASTER ENGINE] Module Unloaded")
    print(f"  Module Name: {module_name}")
    return 0


def reload_module(
    module_name: str,
    loader_manager: object | None = None,
) -> int:
    """Reload a dynamic module package."""
    bootstrap = Bootstrap().build()
    manager = loader_manager or bootstrap.loader_manager()
    try:
        reloaded_name = manager.reload(module_name)
    except Exception as exc:  # noqa: BLE001
        print("[MASTER ENGINE] ReloadModule failed")
        print(f"  message: {exc}")
        return 1

    print("[MASTER ENGINE] Module Reloaded")
    print(f"  Module Name: {reloaded_name}")
    return 0


def create_plugin(path: str) -> int:
    """Create a plugin package template using the SDK."""
    from sdk.templates import create_plugin_template
    from sdk.version import PLUGIN_SDK_VERSION

    try:
        package_dir = create_plugin_template(path)
    except ValueError as exc:
        print("[MASTER ENGINE] CreatePlugin failed")
        print(f"  message: {exc}")
        return 1

    print("[MASTER ENGINE] Plugin Template Created")
    print(f"  Path:        {package_dir}")
    print(f"  SDK Version: {PLUGIN_SDK_VERSION}")
    return 0


def validate_plugin(path: str) -> int:
    """Validate a plugin package using the SDK."""
    from sdk.validation import ValidationError, validate_plugin_package
    from sdk.version import PLUGIN_SDK_VERSION

    try:
        manifest = validate_plugin_package(path)
    except ValidationError as exc:
        print("[MASTER ENGINE] ValidatePlugin failed")
        print(f"  message: {exc}")
        return 1

    print("[MASTER ENGINE] Plugin Validated")
    print(f"  Name:         {manifest.name}")
    print(f"  Version:      {manifest.version}")
    print(f"  Author:       {manifest.author}")
    print(f"  Capabilities: {', '.join(manifest.capabilities)}")
    print(f"  SDK Version:  {manifest.sdk_version or PLUGIN_SDK_VERSION}")
    return 0


def certify_plugin(plugin_path: str) -> int:
    """Certify a plugin package and print the certification report."""
    from core.plugins.certification.compatibility import map_result_to_compatibility_level
    from core.plugins.certification.factory import create_default_plugin_certification_suite
    from core.plugins.certification.loading import (
        CertificationLoadError,
        load_plugin_for_certification,
    )

    try:
        plugin, loader = load_plugin_for_certification(plugin_path)
    except CertificationLoadError as exc:
        print("[MASTER ENGINE] CertifyPlugin failed")
        print(f"  message: {exc}")
        return 1

    try:
        result = create_default_plugin_certification_suite().certify(plugin)
    finally:
        loader.unload(plugin.name())

    compatibility = map_result_to_compatibility_level(result)

    print("[MASTER ENGINE] Plugin Certification")
    print(f"  Plugin ID:           {result.plugin_id}")
    print(f"  Passed:              {result.passed}")
    print(f"  Compatibility Level: {compatibility.value}")
    print("  Errors:")
    if result.errors:
        for error in result.errors:
            print(f"    - {error}")
    else:
        print("    (none)")
    print("  Warnings:")
    if result.warnings:
        for warning in result.warnings:
            print(f"    - {warning}")
    else:
        print("    (none)")
    print("  Checks:")
    if result.checks:
        for check in result.checks:
            print(f"    - {check}")
    else:
        print("    (none)")

    return 0 if result.passed else 1


def register_certified(
    plugin_path: str,
    certification_gate: object | None = None,
    certified_registry: object | None = None,
    *,
    registry_path: str | None = None,
) -> int:
    """Certify a plugin and register it in the certified plugin registry."""
    from core.plugins.certification.gate import CertificationGate
    from core.plugins.certification.loading import (
        CertificationLoadError,
        load_plugin_for_certification,
    )

    bootstrap = Bootstrap().build()
    registry = _resolve_certified_registry(
        bootstrap,
        certified_registry=certified_registry,
        registry_path=registry_path,
    )

    try:
        plugin, loader = load_plugin_for_certification(plugin_path)
        gate = certification_gate or CertificationGate(registry=registry)
        result = gate.evaluate(plugin)
        if not result.passed:
            print("[MASTER ENGINE] RegisterCertified failed")
            print(f"  Plugin ID: {result.plugin_id}")
            for error in result.errors:
                print(f"  message: {error}")
            return 1
        record = gate.certify_and_register(plugin, result=result)
    except CertificationLoadError as exc:
        print("[MASTER ENGINE] RegisterCertified failed")
        print(f"  message: {exc}")
        return 1
    finally:
        if "plugin" in locals():
            loader.unload(plugin.name())

    print("[MASTER ENGINE] Certified Plugin Registered")
    print(f"  Plugin ID:           {record.plugin_id}")
    print(f"  Version:             {record.version}")
    print(f"  Certified:           {record.certified}")
    print(f"  Compatibility Level: {record.compatibility_level.value}")
    print(f"  Registry Path:       {_resolve_registry_path(registry_path)}")
    return 0


def list_certified(
    *,
    registry_path: str | None = None,
    certified_registry: object | None = None,
) -> int:
    """List certified plugins from the registry."""
    bootstrap = Bootstrap().build()
    registry = _resolve_certified_registry(
        bootstrap,
        certified_registry=certified_registry,
        registry_path=registry_path,
    )
    records = registry.list_all()

    print("[MASTER ENGINE] Certified Plugins")
    if not records:
        print("No certified plugins.")
        return 0

    for record in records:
        print(f"  Plugin ID:     {record.plugin_id}")
        print(f"  Version:       {record.version}")
        print(f"  Compatibility: {record.compatibility_level.value}")
        print(f"  Certified:     {record.certified}")
        print(f"  Warnings:      {len(record.warnings)}")
        print(f"  Checks:        {len(record.checks)}")
        print()
    return 0


def is_certified(
    plugin_id: str,
    *,
    registry_path: str | None = None,
    certified_registry: object | None = None,
) -> int:
    """Check whether a plugin is certified in the registry."""
    bootstrap = Bootstrap().build()
    registry = _resolve_certified_registry(
        bootstrap,
        certified_registry=certified_registry,
        registry_path=registry_path,
    )
    record = registry.get(plugin_id)

    if record is not None and record.certified:
        print("[MASTER ENGINE] Plugin Certified")
        print(f"  Plugin ID:           {record.plugin_id}")
        print(f"  Version:             {record.version}")
        print(f"  Compatibility Level: {record.compatibility_level.value}")
        print(f"  Certified:           {record.certified}")
        return 0

    print("[MASTER ENGINE] Plugin Not Certified")
    print(f"  Plugin ID: {plugin_id}")
    return 1


def unregister_certified(
    plugin_id: str,
    *,
    registry_path: str | None = None,
    certified_registry: object | None = None,
) -> int:
    """Remove a plugin from the certified plugin registry."""
    bootstrap = Bootstrap().build()
    registry = _resolve_certified_registry(
        bootstrap,
        certified_registry=certified_registry,
        registry_path=registry_path,
    )
    resolved_path = _resolve_registry_path(registry_path)
    registry.delete(plugin_id)

    print("[MASTER ENGINE] Certified Plugin Unregistered")
    print(f"  Plugin ID:     {plugin_id}")
    print(f"  Registry Path: {resolved_path}")
    return 0


def list_audit_log(*, audit_path: str | None = None) -> int:
    """List registry audit log entries."""
    logger = _resolve_audit_logger(audit_path)
    entries = logger.list_entries()

    print("[MASTER ENGINE] Registry Audit Log")
    if not entries:
        print("No audit entries.")
        return 0

    for entry in entries:
        print(f"  Timestamp: {entry.timestamp}")
        print(f"  Action:    {entry.action}")
        print(f"  Plugin ID: {entry.plugin_id}")
        print(f"  Version:   {entry.version}")
        print(f"  Result:    {entry.result}")
        print()
    return 0


def clear_audit_log(*, audit_path: str | None = None) -> int:
    """Clear registry audit log entries."""
    logger = _resolve_audit_logger(audit_path)
    logger.clear()

    print("[MASTER ENGINE] Registry Audit Log Cleared")
    if audit_path:
        print(f"  Audit Path: {audit_path}")
    return 0


def list_capabilities() -> int:
    """List analysis capabilities from registered plugins."""
    bootstrap = Bootstrap().build()
    result = bootstrap.query_bus().execute(ListCapabilities(metadata=_metadata()))

    if isinstance(result, Failure):
        _print_failure("ListCapabilities", result.unwrap_error())
        return 1

    capabilities = result.unwrap()
    print("[MASTER ENGINE] Registered capabilities")
    for capability in capabilities:
        print(f"  {capability}")
    return 0


def list_providers() -> int:
    """List registered providers from the provider catalog."""
    bootstrap = Bootstrap().build()
    result = bootstrap.query_bus().execute(ListProviders(metadata=_metadata()))

    if isinstance(result, Failure):
        _print_failure("ListProviders", result.unwrap_error())
        return 1

    providers = result.unwrap()
    print("[MASTER ENGINE] Registered providers")
    for item in providers:
        capabilities = ", ".join(item.capabilities)
        enabled = "enabled" if item.enabled else "disabled"
        print(
            f"  {item.provider_id} | {item.name} | {item.model} | "
            f"{capabilities} | {enabled}",
        )
    return 0


def generate_text(provider_id: str, prompt: str) -> int:
    """Dispatch GenerateText to a provider stub."""
    bootstrap = Bootstrap().build()
    try:
        command = GenerateText(
            metadata=_metadata(),
            provider_id=ProviderId(value=provider_id),
            prompt=prompt,
        )
    except ValueError as exc:
        print("[MASTER ENGINE] GenerateText validation failed")
        print(f"  message: {exc}")
        return 1

    result = bootstrap.command_bus().dispatch(command)
    if isinstance(result, Failure):
        _print_failure("GenerateText", result.unwrap_error())
        return 1

    text = result.unwrap()
    print("[MASTER ENGINE] GenerateText completed")
    print(f"  provider_id: {provider_id}")
    print(f"  response:    {text}")
    return 0


def _parse_load_module_options(
    args: list[str],
) -> tuple[str | None, bool, str | None, bool]:
    certified_only = False
    require_registered = False
    registry_path: str | None = None
    path: str | None = None
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--certified-only":
            certified_only = True
            index += 1
            continue
        if token == "--require-registered":
            require_registered = True
            index += 1
            continue
        if token == "--registry-path" and index + 1 < len(args):
            registry_path = args[index + 1]
            index += 2
            continue
        path = token
        index += 1
    return path, certified_only, registry_path, require_registered


def _parse_registry_path_options(args: list[str]) -> tuple[str | None, list[str]]:
    registry_path: str | None = None
    remaining: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--registry-path" and index + 1 < len(args):
            registry_path = args[index + 1]
            index += 2
            continue
        remaining.append(token)
        index += 1
    return registry_path, remaining


def _parse_audit_path_options(args: list[str]) -> tuple[str | None, list[str]]:
    audit_path: str | None = None
    remaining: list[str] = []
    index = 0
    while index < len(args):
        token = args[index]
        if token == "--audit-path" and index + 1 < len(args):
            audit_path = args[index + 1]
            index += 2
            continue
        remaining.append(token)
        index += 1
    return audit_path, remaining


def _resolve_audit_logger(audit_path: str | None = None) -> object:
    from core.plugins.registry.audit import RegistryAuditLogger, get_default_audit_logger
    from core.plugins.registry.audit_json_store import JsonRegistryAuditStore
    from core.plugins.registry.paths import ensure_default_audit_file

    if audit_path:
        return RegistryAuditLogger(store=JsonRegistryAuditStore(audit_path))
    return get_default_audit_logger()


def _resolve_certified_registry(
    bootstrap: Bootstrap,
    *,
    certified_registry: object | None = None,
    registry_path: str | None = None,
) -> object:
    from core.plugins.registry.factory import create_json_certified_plugin_registry
    from core.plugins.registry.resolver import resolve_certified_registry

    if certified_registry is not None:
        return certified_registry
    if registry_path:
        return create_json_certified_plugin_registry(registry_path)
    return resolve_certified_registry(bootstrap.container())


def _resolve_registry_path(registry_path: str | None = None) -> str:
    from core.plugins.registry.paths import (
        ensure_default_registry_directory,
        ensure_default_registry_file,
    )

    if registry_path:
        return registry_path
    ensure_default_registry_directory()
    return str(ensure_default_registry_file())


def main(argv: list[str] | None = None) -> None:
    """CLI entry point."""
    args = sys.argv[1:] if argv is None else argv

    if not args:
        raise SystemExit(run_dev_analysis())
    if args[0] == "list-capabilities":
        raise SystemExit(list_capabilities())
    if args[0] == "list-providers":
        raise SystemExit(list_providers())
    if args[0] == "generate-text":
        if len(args) < 3:
            print(
                "Usage: python -m core.cli.main generate-text "
                "<provider_id> <prompt>",
            )
            raise SystemExit(1)
        raise SystemExit(generate_text(args[1], args[2]))
    if args[0] == "run-analysis":
        capability, provider_id = _parse_run_analysis_options(args[1:])
        raise SystemExit(run_analysis(capability=capability, provider_id=provider_id))
    if args[0] == "explain-analysis":
        capability, provider_id = _parse_run_analysis_options(
            args[1:] or ["--capability", "wealth.analysis", "--provider-id", "openai.stub"],
        )
        raise SystemExit(explain_analysis(capability=capability, provider_id=provider_id))
    if args[0] == "render-report":
        capability, provider_id = _parse_run_analysis_options(args[1:])
        raise SystemExit(render_report(capability=capability, provider_id=provider_id))
    if args[0] == "export-report":
        export_format, capability, provider_id = _parse_export_report_options(args[1:])
        raise SystemExit(
            export_report(
                export_format=export_format,
                capability=capability,
                provider_id=provider_id,
            ),
        )
    if args[0] == "run-workflow":
        capabilities, provider_id, export_format = _parse_run_workflow_options(args[1:])
        raise SystemExit(
            run_workflow(
                capabilities=capabilities,
                provider_id=provider_id,
                export_format=export_format,
            ),
        )
    if args[0] == "show-events":
        raise SystemExit(show_events())
    if args[0] == "replay-events":
        aggregate_id = _parse_replay_events_options(args[1:])
        raise SystemExit(replay_events(aggregate_id=aggregate_id))
    if args[0] == "snapshot-status":
        raise SystemExit(snapshot_status())
    if args[0] == "event-store-info":
        raise SystemExit(event_store_info())
    if args[0] == "transaction-status":
        raise SystemExit(transaction_status())
    if args[0] == "show-metrics":
        raise SystemExit(show_metrics())
    if args[0] == "list-modules":
        raise SystemExit(list_modules())
    if args[0] == "module-info":
        if len(args) < 2:
            print("Usage: python -m core.cli.main module-info <module_name>")
            raise SystemExit(1)
        raise SystemExit(module_info(args[1]))
    if args[0] == "load-module":
        path, certified_only, registry_path, require_registered = _parse_load_module_options(
            args[1:],
        )
        if path is None:
            print(
                "Usage: python -m core.cli.main load-module "
                "[--certified-only] [--registry-path <path>] "
                "[--require-registered] <package_path>",
            )
            raise SystemExit(1)
        raise SystemExit(
            load_module(
                path,
                certified_only=certified_only,
                registry_path=registry_path,
                require_registered=require_registered,
            ),
        )
    if args[0] == "unload-module":
        if len(args) < 2:
            print("Usage: python -m core.cli.main unload-module <module_name>")
            raise SystemExit(1)
        raise SystemExit(unload_module(args[1]))
    if args[0] == "reload-module":
        if len(args) < 2:
            print("Usage: python -m core.cli.main reload-module <module_name>")
            raise SystemExit(1)
        raise SystemExit(reload_module(args[1]))
    if args[0] == "create-plugin":
        if len(args) < 2:
            print("Usage: python -m core.cli.main create-plugin <package_path>")
            raise SystemExit(1)
        raise SystemExit(create_plugin(args[1]))
    if args[0] == "validate-plugin":
        if len(args) < 2:
            print("Usage: python -m core.cli.main validate-plugin <package_path>")
            raise SystemExit(1)
        raise SystemExit(validate_plugin(args[1]))
    if args[0] == "certify-plugin":
        if len(args) < 2:
            print("Usage: python -m core.cli.main certify-plugin <plugin_path>")
            raise SystemExit(1)
        raise SystemExit(certify_plugin(args[1]))
    if args[0] == "register-certified":
        registry_path, remaining = _parse_registry_path_options(args[1:])
        if not remaining:
            print(
                "Usage: python -m core.cli.main register-certified "
                "[--registry-path <path>] <plugin_path>",
            )
            raise SystemExit(1)
        raise SystemExit(
            register_certified(remaining[0], registry_path=registry_path),
        )
    if args[0] == "list-certified":
        registry_path, remaining = _parse_registry_path_options(args[1:])
        if remaining:
            print(
                "Usage: python -m core.cli.main list-certified "
                "[--registry-path <path>]",
            )
            raise SystemExit(1)
        raise SystemExit(list_certified(registry_path=registry_path))
    if args[0] == "is-certified":
        registry_path, remaining = _parse_registry_path_options(args[1:])
        if len(remaining) != 1:
            print(
                "Usage: python -m core.cli.main is-certified "
                "[--registry-path <path>] <plugin_id>",
            )
            raise SystemExit(1)
        raise SystemExit(
            is_certified(remaining[0], registry_path=registry_path),
        )
    if args[0] == "unregister-certified":
        registry_path, remaining = _parse_registry_path_options(args[1:])
        if len(remaining) != 1:
            print(
                "Usage: python -m core.cli.main unregister-certified "
                "[--registry-path <path>] <plugin_id>",
            )
            raise SystemExit(1)
        raise SystemExit(
            unregister_certified(remaining[0], registry_path=registry_path),
        )
    if args[0] == "list-audit-log":
        audit_path, remaining = _parse_audit_path_options(args[1:])
        if remaining:
            print(
                "Usage: python -m core.cli.main list-audit-log "
                "[--audit-path <path>]",
            )
            raise SystemExit(1)
        raise SystemExit(list_audit_log(audit_path=audit_path))
    if args[0] == "clear-audit-log":
        audit_path, remaining = _parse_audit_path_options(args[1:])
        if remaining:
            print(
                "Usage: python -m core.cli.main clear-audit-log "
                "[--audit-path <path>]",
            )
            raise SystemExit(1)
        raise SystemExit(clear_audit_log(audit_path=audit_path))

    print(f"[MASTER ENGINE] Unknown command: {args[0]}")
    print(
        "Available commands: run-analysis, explain-analysis, render-report, "
        "export-report, run-workflow, show-events, replay-events, "
        "snapshot-status, event-store-info, transaction-status, show-metrics, "
        "list-modules, module-info, load-module, unload-module, reload-module, "
        "create-plugin, validate-plugin, certify-plugin, register-certified, "
        "list-certified, is-certified, unregister-certified, list-audit-log, "
        "clear-audit-log, list-capabilities, list-providers, generate-text",
    )
    raise SystemExit(1)


if __name__ == "__main__":
    main()
