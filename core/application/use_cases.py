"""Application use cases."""

from __future__ import annotations

import time

from dataclasses import replace
from typing import Any, Protocol

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
from core.application.queries import (
    GetAnalysisSession,
    GetEventsByAggregate,
    GetEventsByType,
    GetReport,
    ListCapabilities,
    ListProviders,
    ListReports,
)
from core.application.analysis_pipeline import AnalysisPipeline
from core.application.result import Failure, Result, ResultValue
from core.common.error_codes import ErrorCode
from core.domain.events import DomainEvent
from core.domain.ids import ProviderId, SessionId
from core.domain.report import Report
from core.domain.session import AnalysisSession
from core.domain.value_objects import EngineContext
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus
from core.events.event_types import (
    AnalysisCompleted,
    AnalysisStarted,
    CapabilityExecuted,
    ProviderCalled,
    ProviderCompleted,
)
from core.events.helpers import publish_event, trace_for_event
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector
from core.metrics.recording import MetricsRecorder, elapsed_milliseconds
from core.domain.models import AnalysisResult, TraceStep
from core.provider.errors import ProviderGenerationError, ProviderNotFoundError
from core.provider.metadata import ProviderMetadata


class EngineRunner(Protocol):
    """Minimal engine surface required by RunAnalysisUseCase."""

    def run_analysis(self, request: EngineRunRequest) -> EngineRunResponse: ...


class SupportsProviderCatalog(Protocol):
    """Minimal provider manager surface for provider catalog and validation."""

    @property
    def registry(self) -> object: ...


class SupportsCapabilityValidation(Protocol):
    """Minimal capability catalog surface for RunAnalysis validation."""

    def validate(self, capability: str) -> Failure | None: ...


class SupportsPluginExecution(Protocol):
    """Minimal plugin manager surface for analysis pipeline execution."""

    def execute_analysis_section(self, capability: str, input_data: dict[str, Any]) -> object: ...


class SupportsUnitOfWork(Protocol):
    """Minimal unit-of-work surface required by use cases."""

    sessions: object
    reports: object
    event_store: object

    def register_new(self, aggregate: object) -> None: ...

    def register_dirty(self, aggregate: object) -> None: ...

    def commit(self) -> None: ...


def _domain_failure(exc: ValueError) -> Failure:
    return Result.fail(code="DOMAIN_VALIDATION_ERROR", message=str(exc))


def _not_found(resource: str, identifier: object) -> Failure:
    return Result.fail(
        code="NOT_FOUND",
        message=f"{resource} not found: {identifier}",
    )


def _validate_provider(
    provider_manager: SupportsProviderCatalog,
    provider_id: ProviderId,
) -> Failure | None:
    registry = provider_manager.registry
    if not registry.exists(provider_id):
        return Result.fail(
            code=ErrorCode.PROVIDER_NOT_FOUND,
            message=f"Provider not found: {provider_id}",
        )
    provider = registry.get(provider_id)
    if not provider.metadata().enabled:
        return Result.fail(
            code=ErrorCode.PROVIDER_DISABLED,
            message=f"Provider is disabled: {provider_id}",
        )
    return None


def _validate_capability(
    capability_catalog: SupportsCapabilityValidation,
    capability: str,
) -> Failure | None:
    return capability_catalog.validate(capability)


def _validate_run_analysis_provider(
    provider_manager: SupportsProviderCatalog,
    provider_id: ProviderId,
) -> Failure | None:
    return _validate_provider(provider_manager, provider_id)


def _build_run_analysis_plugin_input(command: RunAnalysis) -> dict[str, Any]:
    return {
        "capability": command.capability,
        "user_id": str(command.user_id),
        "session_id": str(command.session_id),
        "birth_data": {
            "year": command.birth_data.year,
            "month": command.birth_data.month,
            "day": command.birth_data.day,
            "hour": command.birth_data.hour,
            "minute": command.birth_data.minute,
        },
    }


class CreateAnalysisSessionUseCase:
    """Create and persist a new analysis session."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateAnalysisSession) -> ResultValue[AnalysisSession]:
        try:
            context = EngineContext(
                user_id=command.user_id,
                session_id=SessionId.new(),
            )
            session = AnalysisSession.create(
                user_id=command.user_id,
                birth_data=command.birth_data,
                context=context,
            )
            self._uow.register_new(session)
            self._uow.commit()
            return Result.ok(session)
        except ValueError as exc:
            return _domain_failure(exc)


class StartAnalysisSessionUseCase:
    """Transition a session to RUNNING."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: StartAnalysisSession) -> ResultValue[AnalysisSession]:
        session = self._uow.sessions.get(command.session_id)
        if session is None:
            return _not_found("AnalysisSession", command.session_id)
        try:
            session.mark_running()
            self._uow.register_dirty(session)
            self._uow.commit()
            return Result.ok(session)
        except ValueError as exc:
            return _domain_failure(exc)


class CompleteAnalysisSessionUseCase:
    """Transition a session to COMPLETED."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CompleteAnalysisSession) -> ResultValue[AnalysisSession]:
        session = self._uow.sessions.get(command.session_id)
        if session is None:
            return _not_found("AnalysisSession", command.session_id)
        try:
            session.mark_completed()
            self._uow.register_dirty(session)
            self._uow.commit()
            return Result.ok(session)
        except ValueError as exc:
            return _domain_failure(exc)


class FailAnalysisSessionUseCase:
    """Transition a session to FAILED."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: FailAnalysisSession) -> ResultValue[AnalysisSession]:
        session = self._uow.sessions.get(command.session_id)
        if session is None:
            return _not_found("AnalysisSession", command.session_id)
        try:
            session.mark_failed(command.reason)
            self._uow.register_dirty(session)
            self._uow.commit()
            return Result.ok(session)
        except ValueError as exc:
            return _domain_failure(exc)


class CreateReportUseCase:
    """Create and persist a new report."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CreateReport) -> ResultValue[Report]:
        session = self._uow.sessions.get(command.session_id)
        if session is None:
            return _not_found("AnalysisSession", command.session_id)
        try:
            report = Report.create(session_id=command.session_id)
            self._uow.register_new(report)
            self._uow.commit()
            return Result.ok(report)
        except ValueError as exc:
            return _domain_failure(exc)


class AddReportSectionUseCase:
    """Append a section to a report."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: AddReportSection) -> ResultValue[Report]:
        report = self._uow.reports.get(command.report_id)
        if report is None:
            return _not_found("Report", command.report_id)
        try:
            report.add_section(command.section)
            self._uow.register_dirty(report)
            self._uow.commit()
            return Result.ok(report)
        except ValueError as exc:
            return _domain_failure(exc)


class AddExplanationTraceUseCase:
    """Attach an explanation trace to a report."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: AddExplanationTrace) -> ResultValue[Report]:
        report = self._uow.reports.get(command.report_id)
        if report is None:
            return _not_found("Report", command.report_id)
        try:
            report.add_explanation_trace(command.trace)
            self._uow.register_dirty(report)
            self._uow.commit()
            return Result.ok(report)
        except ValueError as exc:
            return _domain_failure(exc)


class CompleteReportUseCase:
    """Mark a report as completed."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, command: CompleteReport) -> ResultValue[Report]:
        report = self._uow.reports.get(command.report_id)
        if report is None:
            return _not_found("Report", command.report_id)
        try:
            report.mark_completed()
            self._uow.register_dirty(report)
            self._uow.commit()
            return Result.ok(report)
        except ValueError as exc:
            return _domain_failure(exc)


class RunAnalysisUseCase:
    """Execute a full analysis run via the engine adapter."""

    def __init__(
        self,
        engine_adapter: EngineRunner,
        plugin_manager: SupportsPluginExecution | None = None,
        provider_manager: SupportsProviderCatalog | None = None,
        capability_catalog: SupportsCapabilityValidation | None = None,
        analysis_pipeline: AnalysisPipeline | None = None,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> None:
        self._engine_adapter = engine_adapter
        self._plugin_manager = plugin_manager
        self._provider_manager = provider_manager
        self._capability_catalog = capability_catalog
        self._analysis_pipeline = analysis_pipeline
        self._event_bus = event_bus
        self._metrics = MetricsRecorder(metrics_collector)

    def execute(self, command: RunAnalysis) -> ResultValue[EngineRunResponse]:
        self._metrics.increment("analysis.started")
        started_at = time.perf_counter()
        result = self._execute(command)
        if isinstance(result, Failure):
            self._metrics.increment("analysis.failed")
        else:
            self._metrics.increment("analysis.completed")
        self._metrics.record_duration(
            "analysis.duration",
            elapsed_milliseconds(started_at),
        )
        return result

    def _execute(self, command: RunAnalysis) -> ResultValue[EngineRunResponse]:
        started = publish_event(
            self._event_bus,
            AnalysisStarted(
                aggregate_id=str(command.session_id),
                payload={
                    "session_id": str(command.session_id),
                    "capability": command.capability,
                },
            ),
        )
        event_traces = [
            trace_for_event(
                started,
                step=TraceStep.REPORT,
                source="analysis",
                message="Analysis started",
            ),
        ]

        if command.provider_id is not None:
            if self._provider_manager is None:
                return Result.fail(
                    code=ErrorCode.PROVIDER_NOT_CONFIGURED,
                    message="Provider manager is not configured.",
                )
            validation_error = _validate_run_analysis_provider(
                self._provider_manager,
                command.provider_id,
            )
            if validation_error is not None:
                return validation_error
            provider_called = publish_event(
                self._event_bus,
                ProviderCalled(
                    aggregate_id=str(command.provider_id),
                    payload={
                        "provider_id": str(command.provider_id),
                        "capability": command.capability,
                    },
                ),
            )
            self._metrics.increment("provider.called")
            event_traces.append(
                trace_for_event(
                    provider_called,
                    step=TraceStep.PROVIDER,
                    source=str(command.provider_id),
                    message="Provider called",
                ),
            )

        if self._capability_catalog is not None:
            capability_error = _validate_capability(
                self._capability_catalog,
                command.capability,
            )
            if capability_error is not None:
                return capability_error

        analysis_result = None
        if self._plugin_manager is not None:
            pipeline = self._analysis_pipeline or AnalysisPipeline(
                self._plugin_manager,
                self._provider_manager,
            )
            try:
                analysis_result = pipeline.run(
                    capability=command.capability,
                    input_data=_build_run_analysis_plugin_input(command),
                    provider_id=command.provider_id,
                )
            except RuntimeError as exc:
                return Result.fail(
                    code=ErrorCode.PROVIDER_NOT_CONFIGURED,
                    message=str(exc),
                )

            if analysis_result is not None:
                capability_executed = publish_event(
                    self._event_bus,
                    CapabilityExecuted(
                        aggregate_id=command.capability,
                        payload={"capability": command.capability},
                    ),
                )
                self._metrics.increment("capability.executed")
                event_traces.append(
                    trace_for_event(
                        capability_executed,
                        step=TraceStep.PLUGIN,
                        source=command.capability,
                        message="Capability executed",
                    ),
                )
                if (
                    command.provider_id is not None
                    and len(analysis_result.sections) > 1
                ):
                    provider_completed = publish_event(
                        self._event_bus,
                        ProviderCompleted(
                            aggregate_id=str(command.provider_id),
                            payload={
                                "provider_id": str(command.provider_id),
                                "capability": command.capability,
                            },
                        ),
                    )
                    self._metrics.increment("provider.completed")
                    event_traces.append(
                        trace_for_event(
                            provider_completed,
                            step=TraceStep.PROVIDER,
                            source=str(command.provider_id),
                            message="Provider completed",
                        ),
                    )
                analysis_result = AnalysisResult(
                    sections=analysis_result.sections,
                    trace=analysis_result.trace + tuple(event_traces),
                )

        request = EngineRunRequest(
            session_id=command.session_id,
            user_id=command.user_id,
            birth_data=command.birth_data,
            context=command.context,
            capability=command.capability,
            provider_id=command.provider_id,
            analysis_result=analysis_result,
        )
        try:
            response = self._engine_adapter.run_analysis(request)
        except Exception as exc:  # noqa: BLE001
            return Result.fail(code=ErrorCode.ENGINE_NOT_READY, message=str(exc))

        if response.status is EngineStatus.FAILED:
            primary_error = response.errors[0] if response.errors else None
            return Result.fail(
                code=primary_error.code if primary_error else ErrorCode.ENGINE_RUN_FAILED,
                message=primary_error.message if primary_error else "Engine run failed.",
                details=primary_error.details if primary_error else None,
            )

        completed = publish_event(
            self._event_bus,
            AnalysisCompleted(
                aggregate_id=str(command.session_id),
                payload={
                    "session_id": str(command.session_id),
                    "capability": command.capability,
                    "status": response.status.value,
                },
            ),
        )
        if response.analysis_result is not None:
            response = replace(
                response,
                analysis_result=AnalysisResult(
                    sections=response.analysis_result.sections,
                    trace=response.analysis_result.trace
                    + (
                        trace_for_event(
                            completed,
                            step=TraceStep.REPORT,
                            source="analysis",
                            message="Analysis completed",
                        ),
                    ),
                ),
            )

        return Result.ok(response)


class SupportsProviderCommands(Protocol):
    """Minimal provider manager surface for provider commands."""

    @property
    def registry(self) -> object: ...

    def generate(
        self,
        provider_id: ProviderId,
        prompt: str,
        context: dict[str, Any] | None = None,
    ) -> str: ...


class GenerateTextUseCase:
    """Generate text through a registered provider."""

    def __init__(self, provider_manager: SupportsProviderCommands) -> None:
        self._provider_manager = provider_manager

    def execute(self, command: GenerateText) -> ResultValue[str]:
        validation_error = _validate_provider(
            self._provider_manager,
            command.provider_id,
        )
        if validation_error is not None:
            return validation_error

        try:
            text = self._provider_manager.generate(
                command.provider_id,
                command.prompt,
                command.context,
            )
        except ProviderNotFoundError as exc:
            return Result.fail(code=ErrorCode.PROVIDER_NOT_FOUND, message=str(exc))
        except ProviderGenerationError as exc:
            return Result.fail(
                code=ErrorCode.PROVIDER_GENERATION_FAILED,
                message=str(exc),
            )
        except Exception as exc:  # noqa: BLE001
            return Result.fail(
                code=ErrorCode.PROVIDER_GENERATION_FAILED,
                message=str(exc),
            )
        return Result.ok(text)


class GetAnalysisSessionUseCase:
    """Read a single analysis session."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, query: GetAnalysisSession) -> ResultValue[AnalysisSession]:
        session = self._uow.sessions.get(query.session_id)
        if session is None:
            return _not_found("AnalysisSession", query.session_id)
        return Result.ok(session)


class GetReportUseCase:
    """Read a single report."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, query: GetReport) -> ResultValue[Report]:
        report = self._uow.reports.get(query.report_id)
        if report is None:
            return _not_found("Report", query.report_id)
        return Result.ok(report)


class ListReportsUseCase:
    """List reports with optional session filter."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, query: ListReports) -> ResultValue[list[Report]]:
        reports = self._uow.reports.list()
        if query.session_id is not None:
            reports = [
                report
                for report in reports
                if report.session_id == query.session_id
            ]
        return Result.ok(reports)


class GetEventsByAggregateUseCase:
    """Load events for an aggregate from the event store."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, query: GetEventsByAggregate) -> ResultValue[list[DomainEvent]]:
        events = self._uow.event_store.load_by_aggregate_id(query.aggregate_id)
        return Result.ok(events)


class GetEventsByTypeUseCase:
    """Load events by type from the event store."""

    def __init__(self, uow: SupportsUnitOfWork) -> None:
        self._uow = uow

    def execute(self, query: GetEventsByType) -> ResultValue[list[DomainEvent]]:
        events = self._uow.event_store.load_by_event_type(query.event_type)
        return Result.ok(events)


class SupportsPluginCatalog(Protocol):
    """Minimal plugin manager surface for capability catalog queries."""

    @property
    def registry(self) -> object: ...


class ListCapabilitiesUseCase:
    """List analysis capabilities exposed by registered plugins."""

    def __init__(self, plugin_manager: SupportsPluginCatalog) -> None:
        self._plugin_manager = plugin_manager

    def execute(self, query: ListCapabilities) -> ResultValue[list[str]]:
        capabilities: set[str] = set()
        for plugin in self._plugin_manager.registry.list():
            metadata = plugin.metadata()
            capabilities.update(metadata.capabilities)
        return Result.ok(sorted(capabilities))


class ListProvidersUseCase:
    """List metadata for all registered providers."""

    def __init__(self, provider_manager: SupportsProviderCatalog) -> None:
        self._provider_manager = provider_manager

    def execute(self, query: ListProviders) -> ResultValue[list[ProviderMetadata]]:
        metadata_list = [
            provider.metadata()
            for provider in self._provider_manager.registry.list()
        ]
        return Result.ok(sorted(metadata_list, key=lambda item: str(item.provider_id)))
