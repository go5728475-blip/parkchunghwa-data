"""Transaction metrics recording."""

from __future__ import annotations

import time

from core.metrics.recording import MetricsRecorder, elapsed_milliseconds


class TransactionMetricsSupport:
    """Records transaction lifecycle metrics."""

    def __init__(self, metrics: MetricsRecorder) -> None:
        self._metrics = metrics
        self._started_at: float | None = None

    def on_begin(self) -> None:
        self._metrics.increment("transaction.started")
        self._started_at = time.perf_counter()

    def on_commit(self) -> None:
        self._metrics.increment("transaction.committed")
        self._record_duration()

    def on_rollback(self) -> None:
        self._metrics.increment("transaction.rollback")
        self._record_duration()

    def _record_duration(self) -> None:
        if self._started_at is None:
            return
        self._metrics.record_duration(
            "transaction.duration",
            elapsed_milliseconds(self._started_at),
        )
        self._started_at = None
