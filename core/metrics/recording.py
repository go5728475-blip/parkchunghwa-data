"""Shared helpers for metrics recording."""

from __future__ import annotations

import time

from core.metrics.interfaces import IMetricsCollector


def elapsed_milliseconds(started_at: float) -> float:
    """Return elapsed milliseconds since a perf_counter timestamp."""
    return (time.perf_counter() - started_at) * 1000.0


class MetricsRecorder:
    """Thin wrapper that no-ops when no collector is configured."""

    def __init__(self, collector: IMetricsCollector | None) -> None:
        self._collector = collector

    def increment(self, metric_name: str) -> None:
        if self._collector is not None:
            self._collector.increment(metric_name)

    def record_duration(self, metric_name: str, milliseconds: float) -> None:
        if self._collector is not None:
            self._collector.record_duration(metric_name, milliseconds)

    def record_value(self, metric_name: str, value: float) -> None:
        if self._collector is not None:
            self._collector.record_value(metric_name, value)
