"""Report builder for canonical multi-section rendering."""

from __future__ import annotations

import time

from dataclasses import replace
from datetime import UTC, datetime

from core.domain.built_report import BuiltReport, CapabilityReportGroup, ReportTocEntry
from core.domain.ids import ReportId
from core.domain.models import AnalysisResult, AnalysisSection, SectionSource, TraceEntry, TraceStep
from core.domain.value_objects import ConfidenceScore, ReportSection
from core.events.event_types import ReportBuilt
from core.events.helpers import publish_event, trace_for_event
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector
from core.metrics.recording import MetricsRecorder, elapsed_milliseconds

_CAPABILITY_LABELS: dict[str, str] = {
    "wealth.analysis": "재물",
    "career.analysis": "직업",
    "relationship.analysis": "관계",
    "master_lock.analysis": "MASTER LOCK",
    "stub.analysis": "Stub",
}

_DEFAULT_TITLE = "MASTER ENGINE Analysis Report"
_SUMMARY_CAPABILITY = "summary"


class ReportBuilder:
    """Builds canonical reports from analysis results."""

    def __init__(
        self,
        event_bus: IEventBus | None = None,
        metrics_collector: IMetricsCollector | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._metrics = MetricsRecorder(metrics_collector)

    def build(self, analysis_result: AnalysisResult) -> BuiltReport:
        """Transform an analysis result into a renderable report."""
        capability_order = _capability_order(analysis_result.sections)
        capability_groups = _build_capability_groups(analysis_result.sections, capability_order)
        flat_sections = tuple(
            section
            for group in capability_groups
            for section in group.sections
        )
        return self._finalize_report(
            BuiltReport(
                report_id=ReportId.new(),
                title=_DEFAULT_TITLE,
                summary=_build_summary(analysis_result.sections),
                sections=flat_sections,
                toc=_build_toc(capability_order),
                generated_at=_utc_timestamp(),
                capability_groups=capability_groups,
                trace=analysis_result.trace,
            ),
        )

    def build_many(
        self,
        analysis_results: tuple[AnalysisResult, ...],
        capability_order: tuple[str, ...] | None = None,
        trace: tuple[TraceEntry, ...] | None = None,
    ) -> BuiltReport:
        """Merge multiple analysis results into a single built report."""
        if not analysis_results:
            return self.build_empty()

        sections: list[AnalysisSection] = []
        merged_trace: list[TraceEntry] = []
        for result in analysis_results:
            sections.extend(result.sections)
            merged_trace.extend(result.trace)

        order = (
            list(capability_order)
            if capability_order is not None
            else _capability_order(tuple(sections))
        )
        final_trace = tuple(trace) if trace is not None else tuple(merged_trace)
        capability_groups = _build_capability_groups(tuple(sections), order)
        flat_sections = tuple(
            section
            for group in capability_groups
            for section in group.sections
        )
        return self._finalize_report(
            BuiltReport(
                report_id=ReportId.new(),
                title=_DEFAULT_TITLE,
                summary=_build_summary(tuple(sections)),
                sections=flat_sections,
                toc=_build_toc(order),
                generated_at=_utc_timestamp(),
                capability_groups=capability_groups,
                trace=final_trace,
            ),
        )

    def build_empty(self) -> BuiltReport:
        """Build an empty placeholder report."""
        return self._finalize_report(
            BuiltReport(
                report_id=ReportId.new(),
                title=_DEFAULT_TITLE,
                summary=_build_summary(()),
                sections=(),
                toc=(),
                generated_at=_utc_timestamp(),
                capability_groups=(),
                trace=(),
            ),
        )

    def _finalize_report(self, built_report: BuiltReport) -> BuiltReport:
        started_at = time.perf_counter()
        if self._event_bus is None:
            self._record_report_metrics(started_at)
            return built_report
        event = publish_event(
            self._event_bus,
            ReportBuilt(
                aggregate_id=str(built_report.report_id),
                payload={
                    "report_id": str(built_report.report_id),
                    "title": built_report.title,
                    "section_count": len(built_report.sections),
                },
            ),
        )
        finalized = replace(
            built_report,
            trace=built_report.trace
            + (
                trace_for_event(
                    event,
                    step=TraceStep.REPORT,
                    source="report_builder",
                    message="Report built",
                ),
            ),
        )
        self._record_report_metrics(started_at)
        return finalized

    def _record_report_metrics(self, started_at: float) -> None:
        self._metrics.increment("report.built")
        self._metrics.record_duration(
            "report.duration",
            elapsed_milliseconds(started_at),
        )


def _utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _capability_label(capability: str) -> str:
    return _CAPABILITY_LABELS.get(capability, capability)


def _capability_order(sections: tuple[AnalysisSection, ...]) -> list[str]:
    order: list[str] = []
    for section in sections:
        if section.capability not in order:
            order.append(section.capability)
    return order


def _build_capability_groups(
    sections: tuple[AnalysisSection, ...],
    capability_order: list[str],
) -> tuple[CapabilityReportGroup, ...]:
    grouped: dict[str, list[AnalysisSection]] = {
        capability: [] for capability in capability_order
    }
    for section in sections:
        grouped[section.capability].append(section)

    groups: list[CapabilityReportGroup] = []
    for capability in capability_order:
        ordered_sections = sorted(
            grouped[capability],
            key=_section_sort_key,
        )
        groups.append(
            CapabilityReportGroup(
                capability=capability,
                label=_capability_label(capability),
                sections=tuple(
                    _analysis_section_to_report_section(section)
                    for section in ordered_sections
                ),
            ),
        )
    return tuple(groups)


def _section_sort_key(section: AnalysisSection) -> int:
    if section.source is SectionSource.PLUGIN:
        return 0
    return 1


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


def _build_summary(sections: tuple[AnalysisSection, ...]) -> str:
    plugin_count = sum(
        1 for section in sections if section.source is SectionSource.PLUGIN
    )
    provider_count = sum(
        1 for section in sections if section.source is SectionSource.PROVIDER
    )
    total = len(sections)
    return (
        f"총 {total}개 분석이 수행되었습니다.\n\n"
        f"Plugin {plugin_count}개\n"
        f"Provider 설명 {provider_count}개"
    )


def _build_toc(capability_order: list[str]) -> tuple[ReportTocEntry, ...]:
    entries = [
        ReportTocEntry(
            order=index,
            title=_capability_label(capability),
            capability=capability,
        )
        for index, capability in enumerate(capability_order, start=1)
    ]
    if len(capability_order) > 1:
        entries.append(
            ReportTocEntry(
                order=len(entries) + 1,
                title="종합",
                capability=_SUMMARY_CAPABILITY,
            ),
        )
    return tuple(entries)
