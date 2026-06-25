"""Markdown report exporter."""

from __future__ import annotations

from core.domain.built_report import BuiltReport, CapabilityReportGroup
from core.domain.value_objects import ReportSection
from core.report.exporters.event_support import export_report_with_metrics
from core.report.interfaces import IReportExporter
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector

_PLUGIN_LABEL = "PLUGIN"
_PROVIDER_LABEL = "PROVIDER"


class MarkdownReportExporter(IReportExporter):
    """Exports built reports as Markdown strings."""

    def __init__(
        self,
        event_bus: IEventBus | None = None,
        export_format: str = "markdown",
        metrics_collector: IMetricsCollector | None = None,
    ) -> None:
        self._event_bus = event_bus
        self._export_format = export_format
        self._metrics_collector = metrics_collector

    def export(self, report: BuiltReport) -> str:
        return export_report_with_metrics(
            report,
            self._export_format,
            event_bus=self._event_bus,
            metrics_collector=self._metrics_collector,
            render=lambda: self._render(report),
        )

    def _render(self, report: BuiltReport) -> str:
        lines: list[str] = [f"# {report.title}", "", "## Summary", "", report.summary, ""]

        lines.extend(["## TOC", ""])
        if report.toc:
            for entry in report.toc:
                lines.append(f"{entry.order}. {entry.title}")
        else:
            lines.append("(empty)")
        lines.append("")

        for group in report.capability_groups:
            lines.extend(_render_capability_group(group))

        lines.extend(["## Trace", ""])
        if report.trace:
            for entry in report.trace:
                lines.append(
                    f"- {entry.step.value} | {entry.source} | {entry.timestamp}: "
                    f"{entry.message}",
                )
        else:
            lines.append("(empty)")

        return "\n".join(lines).rstrip() + "\n"


def _render_capability_group(group: CapabilityReportGroup) -> list[str]:
    lines = [f"## {group.label}", ""]
    for section in group.sections:
        lines.extend(_render_section(section))
        lines.append("")
    return lines


def _render_section(section: ReportSection) -> list[str]:
    source_label = "Plugin" if section.generated_by == _PLUGIN_LABEL else "Provider"
    lines = [
        f"### {source_label}",
        "",
        section.title,
        "",
        section.content,
        "",
        "### Confidence",
        "",
        str(section.confidence.value),
        "",
    ]
    if section.reasoning:
        lines.extend(["### Reasoning", ""])
        lines.extend(f"- {step}" for step in section.reasoning)
        lines.append("")
    if section.evidence:
        lines.extend(["### Evidence", ""])
        lines.extend(f"- {item}" for item in section.evidence)
        lines.append("")
    return lines
