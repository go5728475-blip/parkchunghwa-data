"""Stub engine implementation for testing and bootstrap wiring."""

from __future__ import annotations

from typing import Any

from core.bootstrap.configuration import EngineConfiguration
from core.domain.models import AnalysisResult, AnalysisSection, TraceStep
from core.domain.report import Report
from core.domain.session import AnalysisSession
from core.domain.value_objects import ConfidenceScore, ExplanationTrace, ReportSection
from core.domain.xai import (
    build_plugin_analysis_section,
    build_plugin_trace_entry,
    build_report_trace_entry,
    trace_entries_to_reason_steps,
)
from core.engine.kernel import EngineKernel
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus
from core.infrastructure.memory_unit_of_work import InMemoryUnitOfWork
from core.plugin.manager import PluginManager

_STUB_SUMMARY = "Stub result only"
_STUB_SECTION_TITLE = "Stub Section"
_STUB_SECTION_CONTENT = "Stub result only"
_STUB_TRACE_STEPS = ("Stub step 1: placeholder input received", "Stub step 2: stub output produced")


class StubEngine(EngineKernel):
    """Placeholder engine that wires domain aggregates without interpretation."""

    def __init__(
        self,
        unit_of_work: InMemoryUnitOfWork,
        configuration: EngineConfiguration | None = None,
        plugin_manager: PluginManager | None = None,
    ) -> None:
        super().__init__(configuration)
        self._unit_of_work = unit_of_work
        self._plugin_manager = plugin_manager

    def _execute_run(self, request: EngineRunRequest) -> EngineRunResponse:
        if request.analysis_result is not None:
            analysis_result = request.analysis_result
        else:
            analysis_result = self._build_legacy_analysis_result(request)

        session = AnalysisSession.create(
            user_id=request.user_id,
            birth_data=request.birth_data,
            context=request.context,
        )
        self._unit_of_work.register_new(session)
        session.mark_running()
        self._unit_of_work.register_dirty(session)

        report = Report.create(session_id=session.session_id)
        self._unit_of_work.register_new(report)

        for section in analysis_result.sections:
            report.add_section(_analysis_section_to_report_section(section))
        self._unit_of_work.register_dirty(report)

        report_trace = build_report_trace_entry(str(report.report_id))
        full_trace = analysis_result.trace + (report_trace,)
        persisted_result = AnalysisResult(
            sections=analysis_result.sections,
            trace=full_trace,
        )
        trace = ExplanationTrace(reason_steps=trace_entries_to_reason_steps(full_trace))
        report.add_explanation_trace(trace)
        self._unit_of_work.register_dirty(report)

        report.mark_completed()
        self._unit_of_work.register_dirty(report)

        session.mark_completed()
        self._unit_of_work.register_dirty(session)

        self._unit_of_work.commit()

        return EngineRunResponse(
            session_id=session.session_id,
            status=EngineStatus.COMPLETED,
            report_id=report.report_id,
            summary=_STUB_SUMMARY,
            explanation_trace=trace,
            analysis_result=persisted_result,
        )

    def _build_legacy_analysis_result(self, request: EngineRunRequest) -> AnalysisResult:
        if self._plugin_manager is not None:
            input_data = _build_plugin_input(request)
            section = self._plugin_manager.execute_analysis_section(
                request.capability,
                input_data,
            )
            return AnalysisResult(
                sections=(section,),
                trace=(build_plugin_trace_entry(request.capability),),
            )

        section = build_plugin_analysis_section(
            capability=request.capability,
            title=_STUB_SECTION_TITLE,
            content=_STUB_SECTION_CONTENT,
            plugin_id="legacy.stub",
        )
        return AnalysisResult(sections=(section,), trace=())


def _build_plugin_input(request: EngineRunRequest) -> dict[str, Any]:
    return {
        "capability": request.capability,
        "user_id": str(request.user_id),
        "session_id": str(request.session_id),
        "birth_data": {
            "year": request.birth_data.year,
            "month": request.birth_data.month,
            "day": request.birth_data.day,
            "hour": request.birth_data.hour,
            "minute": request.birth_data.minute,
        },
    }


def _analysis_section_to_report_section(section: AnalysisSection) -> ReportSection:
    explanation = section.explanation
    return ReportSection(
        title=f"[{section.source}] {section.title}",
        content=section.content,
        confidence=ConfidenceScore(value=explanation.confidence),
        section_id=str(section.section_id),
        explanation_id=str(explanation.explanation_id),
        generated_by=explanation.generated_by.value,
        reasoning=explanation.reasoning,
        evidence=explanation.evidence,
        enriched_from_section_id=(
            str(section.enriched_from_section_id)
            if section.enriched_from_section_id is not None
            else None
        ),
    )
