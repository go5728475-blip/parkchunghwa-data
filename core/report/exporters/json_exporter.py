"""JSON report exporter."""

from __future__ import annotations

import json

from core.domain.built_report import BuiltReport
from core.report.exporters.event_support import export_report_with_metrics
from core.report.interfaces import IReportExporter
from core.report.serialization import built_report_to_dict
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector


class JsonReportExporter(IReportExporter):
    """Exports built reports as JSON strings."""

    def __init__(
        self,
        event_bus: IEventBus | None = None,
        export_format: str = "json",
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
            render=lambda: json.dumps(
                built_report_to_dict(report),
                ensure_ascii=False,
                indent=2,
            ),
        )
