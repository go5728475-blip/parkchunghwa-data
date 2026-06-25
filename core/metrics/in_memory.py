"""In-memory metrics collector."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.metrics.interfaces import IMetricsCollector, MetricSnapshot


@dataclass
class _MetricAccumulator:
    count: int = 0
    total: float = 0.0
    minimum: float | None = None
    maximum: float | None = None

    def add(self, value: float) -> None:
        self.count += 1
        self.total += value
        self.minimum = value if self.minimum is None else min(self.minimum, value)
        self.maximum = value if self.maximum is None else max(self.maximum, value)

    def to_snapshot(self, metric_name: str) -> MetricSnapshot:
        avg = self.total / self.count if self.count else 0.0
        return MetricSnapshot(
            metric_name=metric_name,
            count=self.count,
            sum=self.total,
            avg=avg,
            min=self.minimum,
            max=self.maximum,
        )


@dataclass
class InMemoryMetricsCollector(IMetricsCollector):
    """Collects operational metrics in process memory."""

    _metrics: dict[str, _MetricAccumulator] = field(default_factory=dict)

    def increment(self, metric_name: str) -> None:
        self._accumulate(metric_name, 1.0)

    def record_duration(self, metric_name: str, milliseconds: float) -> None:
        self._accumulate(metric_name, milliseconds)

    def record_value(self, metric_name: str, value: float) -> None:
        self._accumulate(metric_name, value)

    def get(self, metric_name: str) -> MetricSnapshot | None:
        accumulator = self._metrics.get(metric_name)
        if accumulator is None or accumulator.count == 0:
            return None
        return accumulator.to_snapshot(metric_name)

    def list(self) -> tuple[MetricSnapshot, ...]:
        return tuple(
            accumulator.to_snapshot(metric_name)
            for metric_name, accumulator in sorted(self._metrics.items())
            if accumulator.count > 0
        )

    def clear(self) -> None:
        self._metrics.clear()

    def _accumulate(self, metric_name: str, value: float) -> None:
        accumulator = self._metrics.setdefault(metric_name, _MetricAccumulator())
        accumulator.add(value)
