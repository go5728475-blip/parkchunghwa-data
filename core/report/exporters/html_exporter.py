"""HTML report exporter."""

from __future__ import annotations

from html import escape

from core.domain.built_report import BuiltReport, CapabilityReportGroup
from core.domain.value_objects import ReportSection
from core.report.exporters.event_support import export_report_with_metrics
from core.report.interfaces import IReportExporter
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector

_PLUGIN_LABEL = "PLUGIN"


class HtmlReportExporter(IReportExporter):
    """Exports built reports as semantic HTML5 strings."""

    def __init__(
        self,
        event_bus: IEventBus | None = None,
        export_format: str = "html",
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
        parts = [
            "<!DOCTYPE html>",
            '<html lang="ko">',
            "<head>",
            '<meta charset="utf-8">',
            f"<title>{escape(report.title)}</title>",
            "</head>",
            "<body>",
            "<article>",
            f"<header><h1>{escape(report.title)}</h1></header>",
            _render_summary(report.summary),
            _render_toc(report),
        ]
        for group in report.capability_groups:
            parts.append(_render_capability_group(group))
        parts.append(_render_trace(report))
        parts.extend(["</article>", "</body>", "</html>"])
        return "\n".join(parts)


def _render_summary(summary: str) -> str:
    return (
        "<section>"
        "<h2>Summary</h2>"
        f"<p>{escape(summary)}</p>"
        "</section>"
    )


def _render_toc(report: BuiltReport) -> str:
    lines = ["<section>", "<h2>TOC</h2>"]
    if report.toc:
        lines.append("<ol>")
        for entry in report.toc:
            lines.append(f"<li>{escape(entry.title)}</li>")
        lines.append("</ol>")
    else:
        lines.append("<p>(empty)</p>")
    lines.append("</section>")
    return "\n".join(lines)


def _render_capability_group(group: CapabilityReportGroup) -> str:
    parts = [
        "<section>",
        f"<h2>{escape(group.label)}</h2>",
    ]
    for section in group.sections:
        parts.append(_render_section(section))
    parts.append("</section>")
    return "\n".join(parts)


def _render_section(section: ReportSection) -> str:
    source_label = "Plugin" if section.generated_by == _PLUGIN_LABEL else "Provider"
    parts = [
        "<section>",
        f"<h3>{escape(source_label)}</h3>",
        f"<h4>{escape(section.title)}</h4>",
        f"<p>{escape(section.content)}</p>",
        "<section>",
        "<h3>Confidence</h3>",
        f"<p>{section.confidence.value}</p>",
        "</section>",
    ]
    if section.reasoning:
        parts.extend(
            [
                "<section>",
                "<h3>Reasoning</h3>",
                "<ul>",
                *(f"<li>{escape(step)}</li>" for step in section.reasoning),
                "</ul>",
                "</section>",
            ],
        )
    if section.evidence:
        parts.extend(
            [
                "<section>",
                "<h3>Evidence</h3>",
                "<ul>",
                *(f"<li>{escape(item)}</li>" for item in section.evidence),
                "</ul>",
                "</section>",
            ],
        )
    parts.append("</section>")
    return "\n".join(parts)


def _render_trace(report: BuiltReport) -> str:
    parts = ["<section>", "<h2>Trace</h2>"]
    if report.trace:
        parts.append("<ul>")
        for entry in report.trace:
            parts.append(
                "<li>"
                f"<strong>{escape(entry.step.value)}</strong> "
                f"| {escape(entry.source)} "
                f"| <time>{escape(entry.timestamp)}</time>: "
                f"{escape(entry.message)}"
                "</li>",
            )
        parts.append("</ul>")
    else:
        parts.append("<p>(empty)</p>")
    parts.append("</section>")
    return "\n".join(parts)
