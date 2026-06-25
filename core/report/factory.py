"""Report export factory."""

from __future__ import annotations

from core.report.errors import UnsupportedExportFormat
from core.report.exporters.html_exporter import HtmlReportExporter
from core.report.exporters.json_exporter import JsonReportExporter
from core.report.exporters.markdown_exporter import MarkdownReportExporter
from core.report.interfaces import IReportExporter
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector


_SUPPORTED_FORMATS: dict[str, type[IReportExporter]] = {
    "json": JsonReportExporter,
    "markdown": MarkdownReportExporter,
    "html": HtmlReportExporter,
}


def create_exporter(
    format: str,
    event_bus: IEventBus | None = None,
    metrics_collector: IMetricsCollector | None = None,
) -> IReportExporter:
    """Create an exporter for the requested format."""
    normalized = format.lower().strip()
    exporter_type = _SUPPORTED_FORMATS.get(normalized)
    if exporter_type is None:
        supported = ", ".join(sorted(_SUPPORTED_FORMATS))
        msg = f"Unsupported export format: {format!r}. Supported formats: {supported}."
        raise UnsupportedExportFormat(msg)
    return exporter_type(
        event_bus=event_bus,
        export_format=normalized,
        metrics_collector=metrics_collector,
    )
