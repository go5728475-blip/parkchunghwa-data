"""Tests for in-memory metrics collector."""

from __future__ import annotations

from core.metrics.in_memory import InMemoryMetricsCollector


def test_increment_records_count_and_average() -> None:
    collector = InMemoryMetricsCollector()

    collector.increment("workflow.started")
    collector.increment("workflow.started")

    metric = collector.get("workflow.started")
    assert metric is not None
    assert metric.count == 2
    assert metric.sum == 2.0
    assert metric.avg == 1.0
    assert metric.min == 1.0
    assert metric.max == 1.0


def test_record_duration_tracks_milliseconds() -> None:
    collector = InMemoryMetricsCollector()

    collector.record_duration("workflow.duration", 12.5)
    collector.record_duration("workflow.duration", 27.5)

    metric = collector.get("workflow.duration")
    assert metric is not None
    assert metric.count == 2
    assert metric.sum == 40.0
    assert metric.avg == 20.0
    assert metric.min == 12.5
    assert metric.max == 27.5


def test_record_value_tracks_numeric_samples() -> None:
    collector = InMemoryMetricsCollector()

    collector.record_value("custom.value", 3.0)
    collector.record_value("custom.value", 9.0)

    metric = collector.get("custom.value")
    assert metric is not None
    assert metric.count == 2
    assert metric.avg == 6.0


def test_list_returns_all_metrics_sorted_by_name() -> None:
    collector = InMemoryMetricsCollector()
    collector.increment("analysis.completed")
    collector.increment("workflow.started")

    names = [metric.metric_name for metric in collector.list()]
    assert names == ["analysis.completed", "workflow.started"]


def test_clear_removes_all_metrics() -> None:
    collector = InMemoryMetricsCollector()
    collector.increment("workflow.started")

    collector.clear()

    assert collector.list() == ()
    assert collector.get("workflow.started") is None
