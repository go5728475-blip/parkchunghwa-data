"""Shared export metrics recording."""

from __future__ import annotations

import time
from collections.abc import Callable

from core.domain.built_report import BuiltReport
from core.events.event_types import ReportExported
from core.events.helpers import publish_event
from core.events.interfaces import IEventBus
from core.metrics.interfaces import IMetricsCollector
from core.metrics.recording import MetricsRecorder, elapsed_milliseconds


def export_report_with_metrics(
    report: BuiltReport,
    export_format: str,
    *,
    event_bus: IEventBus | None,
    metrics_collector: IMetricsCollector | None,
    render: Callable[[], str],
) -> str:
    """Publish export events, record metrics, and render report output."""
    metrics = MetricsRecorder(metrics_collector)
    started_at = time.perf_counter()
    publish_report_exported(event_bus, report, export_format)
    output = render()
    metrics.increment("report.exported")
    metrics.record_duration("report.export.duration", elapsed_milliseconds(started_at))
    return output


def publish_report_exported(
    event_bus: IEventBus | None,
    report: BuiltReport,
    export_format: str,
) -> ReportExported | None:
    """Publish a report exported event when a bus is configured."""
    if event_bus is None:
        return None
    return publish_event(
        event_bus,
        ReportExported(
            aggregate_id=str(report.report_id),
            payload={
                "report_id": str(report.report_id),
                "format": export_format,
            },
        ),
    )
