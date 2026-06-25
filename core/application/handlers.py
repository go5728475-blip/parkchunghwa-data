"""Command and query handlers delegating to use cases."""

from __future__ import annotations

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
from core.application.result import ResultValue
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
from core.engine.response import EngineRunResponse
from core.domain.events import DomainEvent
from core.domain.report import Report
from core.domain.session import AnalysisSession
from core.provider.metadata import ProviderMetadata


class CreateAnalysisSessionHandler:
    def __init__(self, use_case: CreateAnalysisSessionUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: CreateAnalysisSession) -> ResultValue[AnalysisSession]:
        return self._use_case.execute(command)


class StartAnalysisSessionHandler:
    def __init__(self, use_case: StartAnalysisSessionUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: StartAnalysisSession) -> ResultValue[AnalysisSession]:
        return self._use_case.execute(command)


class CompleteAnalysisSessionHandler:
    def __init__(self, use_case: CompleteAnalysisSessionUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: CompleteAnalysisSession) -> ResultValue[AnalysisSession]:
        return self._use_case.execute(command)


class FailAnalysisSessionHandler:
    def __init__(self, use_case: FailAnalysisSessionUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: FailAnalysisSession) -> ResultValue[AnalysisSession]:
        return self._use_case.execute(command)


class CreateReportHandler:
    def __init__(self, use_case: CreateReportUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: CreateReport) -> ResultValue[Report]:
        return self._use_case.execute(command)


class AddReportSectionHandler:
    def __init__(self, use_case: AddReportSectionUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: AddReportSection) -> ResultValue[Report]:
        return self._use_case.execute(command)


class AddExplanationTraceHandler:
    def __init__(self, use_case: AddExplanationTraceUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: AddExplanationTrace) -> ResultValue[Report]:
        return self._use_case.execute(command)


class CompleteReportHandler:
    def __init__(self, use_case: CompleteReportUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: CompleteReport) -> ResultValue[Report]:
        return self._use_case.execute(command)


class RunAnalysisCommandHandler:
    def __init__(self, use_case: RunAnalysisUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: RunAnalysis) -> ResultValue[EngineRunResponse]:
        return self._use_case.execute(command)


class GenerateTextCommandHandler:
    def __init__(self, use_case: GenerateTextUseCase) -> None:
        self._use_case = use_case

    def __call__(self, command: GenerateText) -> ResultValue[str]:
        return self._use_case.execute(command)


class GetAnalysisSessionHandler:
    def __init__(self, use_case: GetAnalysisSessionUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: GetAnalysisSession) -> ResultValue[AnalysisSession]:
        return self._use_case.execute(query)


class GetReportHandler:
    def __init__(self, use_case: GetReportUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: GetReport) -> ResultValue[Report]:
        return self._use_case.execute(query)


class ListReportsHandler:
    def __init__(self, use_case: ListReportsUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: ListReports) -> ResultValue[list[Report]]:
        return self._use_case.execute(query)


class ListCapabilitiesQueryHandler:
    def __init__(self, use_case: ListCapabilitiesUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: ListCapabilities) -> ResultValue[list[str]]:
        return self._use_case.execute(query)


class ListProvidersQueryHandler:
    def __init__(self, use_case: ListProvidersUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: ListProviders) -> ResultValue[list[ProviderMetadata]]:
        return self._use_case.execute(query)


class GetEventsByAggregateHandler:
    def __init__(self, use_case: GetEventsByAggregateUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: GetEventsByAggregate) -> ResultValue[list[DomainEvent]]:
        return self._use_case.execute(query)


class GetEventsByTypeHandler:
    def __init__(self, use_case: GetEventsByTypeUseCase) -> None:
        self._use_case = use_case

    def __call__(self, query: GetEventsByType) -> ResultValue[list[DomainEvent]]:
        return self._use_case.execute(query)
