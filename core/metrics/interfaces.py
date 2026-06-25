"""Metrics collector interfaces."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class MetricSnapshot:
    """Aggregated statistics for a single metric."""

    metric_name: str
    count: int
    sum: float
    avg: float
    min: float | None
    max: float | None


class IMetricsCollector(ABC):
    """Port for operational metrics collection."""

    @abstractmethod
    def increment(self, metric_name: str) -> None:
        """Record a counter increment."""

    @abstractmethod
    def record_duration(self, metric_name: str, milliseconds: float) -> None:
        """Record a duration sample in milliseconds."""

    @abstractmethod
    def record_value(self, metric_name: str, value: float) -> None:
        """Record a numeric sample."""

    @abstractmethod
    def get(self, metric_name: str) -> MetricSnapshot | None:
        """Return aggregated statistics for a metric."""

    @abstractmethod
    def list(self) -> tuple[MetricSnapshot, ...]:
        """Return aggregated statistics for all recorded metrics."""

    @abstractmethod
    def clear(self) -> None:
        """Clear all recorded metrics."""
