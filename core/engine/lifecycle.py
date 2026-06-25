"""Engine lifecycle management for repeatable runs."""

from __future__ import annotations

from core.engine.kernel import EngineKernel
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus


class EngineLifecycleError(Exception):
    """Raised when the engine lifecycle cannot proceed."""


class EngineLifecycleManager:
    """Coordinates engine status transitions for consecutive runs."""

    def __init__(self, engine: EngineKernel) -> None:
        self._engine = engine

    @property
    def engine(self) -> EngineKernel:
        return self._engine

    def ensure_ready(self) -> None:
        """Ensure the engine is READY before a new run."""
        status = self._engine.status()
        if status is EngineStatus.RUNNING:
            msg = "Engine is already running."
            raise EngineLifecycleError(msg)
        if status is EngineStatus.READY:
            return
        if status in {EngineStatus.IDLE, EngineStatus.COMPLETED, EngineStatus.FAILED}:
            self._engine.initialize()
            return
        msg = f"Unsupported engine status: {status}"
        raise EngineLifecycleError(msg)

    def reset_if_completed(self) -> None:
        """Re-initialize the engine when a previous run finished or failed."""
        if self._engine.status() in {EngineStatus.COMPLETED, EngineStatus.FAILED}:
            self._engine.initialize()

    def shutdown(self) -> None:
        """Shut down the engine."""
        self._engine.shutdown()

    def run_with_lifecycle(self, request: EngineRunRequest) -> EngineRunResponse:
        """Prepare the engine and execute a run request."""
        self.ensure_ready()
        return self._engine.run(request)
