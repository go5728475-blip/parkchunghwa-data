"""Workflow engine for multi-capability orchestration."""

from __future__ import annotations

import time
from dataclasses import replace
from datetime import UTC, datetime

from core.application.commands import RunAnalysis
from core.application.result import Failure, Result, ResultValue
from core.application.use_cases import RunAnalysisUseCase
from core.domain.ids import ProviderId
from core.domain.models import AnalysisResult, TraceEntry, TraceStep
from core.domain.value_objects import EngineContext
from core.events.event_types import WorkflowCompleted, WorkflowStarted
from core.events.helpers import publish_event, trace_for_event
from core.events.interfaces import IEventBus
from core.metrics.context import (
    CorrelationContext,
    clear_correlation_context,
    get_correlation_id,
    set_correlation_context,
    update_correlation_context,
    utc_timestamp,
)
from core.metrics.interfaces import IMetricsCollector
from core.metrics.recording import MetricsRecorder, elapsed_milliseconds
from core.uow.interfaces import IUnitOfWork
from core.workflow.models import (
    ExecutionMode,
    Workflow,
    WorkflowResult,
    WorkflowRunContext,
)


class WorkflowEngine:
    """Runs workflow capabilities sequentially via RunAnalysisUseCase."""

    def __init__(
        self,
        run_analysis_use_case: RunAnalysisUseCase,
        event_bus: IEventBus | None = None,
        unit_of_work: IUnitOfWork | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> None:
        self._run_analysis = run_analysis_use_case
        self._event_bus = event_bus
        self._unit_of_work = unit_of_work
        self._metrics = MetricsRecorder(metrics_collector)

    def run(
        self,
        workflow: Workflow,
        context: WorkflowRunContext,
        provider_id: ProviderId | None = None,
    ) -> ResultValue[WorkflowResult]:
        """Execute workflow capabilities in order and aggregate results."""
        set_correlation_context(
            CorrelationContext(
                correlation_id=str(context.metadata.correlation_id),
                workflow_id=str(workflow.workflow_id),
                started_at=utc_timestamp(),
            ),
        )
        self._metrics.increment("workflow.started")
        started_at = time.perf_counter()
        try:
            if self._unit_of_work is None:
                result = self._execute(workflow, context, provider_id)
            else:
                result = self._run_with_transaction(workflow, context, provider_id)
            self._record_workflow_outcome(result, started_at)
            return result
        finally:
            clear_correlation_context()

    def _run_with_transaction(
        self,
        workflow: Workflow,
        context: WorkflowRunContext,
        provider_id: ProviderId | None,
    ) -> ResultValue[WorkflowResult]:
        assert self._unit_of_work is not None
        self._unit_of_work.begin()
        update_correlation_context(transaction_id=_transaction_id(self._unit_of_work))
        try:
            result = self._execute(workflow, context, provider_id)
            if isinstance(result, Failure):
                self._unit_of_work.rollback()
                return result
            self._unit_of_work.commit()
            return Result.ok(
                self._merge_transaction_trace(
                    result.unwrap(),
                    self._transaction_trace(),
                ),
            )
        except Exception:
            self._unit_of_work.rollback()
            raise

    def _record_workflow_outcome(
        self,
        result: ResultValue[WorkflowResult],
        started_at: float,
    ) -> None:
        if isinstance(result, Failure):
            self._metrics.increment("workflow.failed")
        else:
            self._metrics.increment("workflow.completed")
        self._metrics.record_duration(
            "workflow.duration",
            elapsed_milliseconds(started_at),
        )

    def _execute(
        self,
        workflow: Workflow,
        context: WorkflowRunContext,
        provider_id: ProviderId | None,
    ) -> ResultValue[WorkflowResult]:
        if workflow.execution_mode is ExecutionMode.PARALLEL:
            # PARALLEL is reserved; sequential execution is used for now.
            pass

        trace_entries: list[TraceEntry] = []
        analysis_results: list[AnalysisResult] = []

        started = publish_event(
            self._event_bus,
            WorkflowStarted(
                aggregate_id=str(workflow.workflow_id),
                payload={
                    "workflow_id": str(workflow.workflow_id),
                    "name": workflow.name,
                    "capabilities": list(workflow.capabilities),
                },
            ),
        )
        trace_entries.append(
            trace_for_event(
                started,
                step=TraceStep.REPORT,
                source="workflow",
                message=f"Workflow started: {workflow.name}",
            ),
        )

        engine_context = EngineContext(
            user_id=context.user_id,
            session_id=context.session_id,
        )

        for capability in workflow.capabilities:
            trace_entries.append(
                _workflow_trace_entry(f"Executing capability: {capability}"),
            )
            try:
                command = RunAnalysis(
                    metadata=context.metadata,
                    session_id=context.session_id,
                    user_id=context.user_id,
                    birth_data=context.birth_data,
                    context=engine_context,
                    capability=capability,
                    provider_id=provider_id,
                )
            except ValueError as exc:
                return Result.fail(
                    code="DOMAIN_VALIDATION_ERROR",
                    message=str(exc),
                )

            result = self._run_analysis.execute(command)
            if isinstance(result, Failure):
                return result

            response = result.unwrap()
            if response.analysis_result is None:
                return Result.fail(
                    code="WORKFLOW_ANALYSIS_FAILED",
                    message=f"No analysis result for capability: {capability}",
                )

            analysis_results.append(response.analysis_result)
            trace_entries.extend(response.analysis_result.trace)
            trace_entries.append(
                _workflow_trace_entry(f"Completed capability: {capability}"),
            )

        completed = publish_event(
            self._event_bus,
            WorkflowCompleted(
                aggregate_id=str(workflow.workflow_id),
                payload={
                    "workflow_id": str(workflow.workflow_id),
                    "capability_count": len(workflow.capabilities),
                },
            ),
        )
        trace_entries.append(
            trace_for_event(
                completed,
                step=TraceStep.REPORT,
                source="workflow",
                message="Workflow completed",
            ),
        )

        return Result.ok(
            WorkflowResult(
                workflow_id=workflow.workflow_id,
                analysis_results=tuple(analysis_results),
                trace=tuple(trace_entries),
            ),
        )

    def _transaction_trace(self) -> tuple[TraceEntry, ...]:
        if self._unit_of_work is None:
            return ()
        trace = getattr(self._unit_of_work, "transaction_trace", ())
        return tuple(trace)

    @staticmethod
    def _merge_transaction_trace(
        workflow_result: WorkflowResult,
        transaction_trace: tuple[TraceEntry, ...],
    ) -> WorkflowResult:
        if not transaction_trace:
            return workflow_result
        return replace(
            workflow_result,
            trace=workflow_result.trace + transaction_trace,
        )


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _workflow_trace_entry(message: str) -> TraceEntry:
    return TraceEntry(
        step=TraceStep.REPORT,
        source="workflow",
        timestamp=_utc_timestamp(),
        message=message,
        correlation_id=get_correlation_id(),
    )


def _transaction_id(unit_of_work: IUnitOfWork) -> str:
    return str(getattr(unit_of_work, "_aggregate_id", "workflow-transaction"))
