"""Workflow report builder integration."""

from __future__ import annotations

from core.application.report_builder import ReportBuilder
from core.domain.built_report import BuiltReport
from core.events.interfaces import IEventBus
from core.workflow.models import Workflow, WorkflowResult


class WorkflowReportBuilder:
    """Builds a unified BuiltReport from workflow execution results."""

    def __init__(
        self,
        report_builder: ReportBuilder | None = None,
        event_bus: IEventBus | None = None,
    ) -> None:
        self._report_builder = report_builder or ReportBuilder(event_bus=event_bus)

    def build(self, workflow: Workflow, workflow_result: WorkflowResult) -> BuiltReport:
        """Merge workflow analysis results into a single built report."""
        return self._report_builder.build_many(
            workflow_result.analysis_results,
            capability_order=workflow.capabilities,
            trace=workflow_result.trace,
        )
