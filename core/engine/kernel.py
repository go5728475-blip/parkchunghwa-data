"""Engine kernel base implementation."""

from __future__ import annotations

from abc import ABC, abstractmethod

from core.bootstrap.configuration import EngineConfiguration
from core.engine.errors import EngineError
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse
from core.engine.status import EngineStatus


class EngineKernelError(Exception):
    """Raised when the engine kernel cannot execute an operation."""


class EngineKernel(ABC):
    """Base engine kernel managing lifecycle without interpretation logic."""

    def __init__(self, configuration: EngineConfiguration | None = None) -> None:
        self._configuration = configuration or EngineConfiguration.default()
        self._status = EngineStatus.IDLE

    def configure(self, configuration: EngineConfiguration) -> None:
        """Apply engine configuration."""
        self._configuration = configuration
        if self._status is not EngineStatus.IDLE:
            self.shutdown()

    def initialize(self) -> None:
        """Prepare the engine for execution."""
        if self._status is EngineStatus.RUNNING:
            msg = "Cannot initialize while the engine is running."
            raise EngineKernelError(msg)
        self._on_initialize()
        self._status = EngineStatus.READY

    def status(self) -> EngineStatus:
        """Return the current engine status."""
        return self._status

    def run(self, request: EngineRunRequest) -> EngineRunResponse:
        """Execute a run request through the kernel lifecycle."""
        if self._status is not EngineStatus.READY:
            msg = "Engine must be initialized and READY before run."
            raise EngineKernelError(msg)

        self._status = EngineStatus.RUNNING
        try:
            response = self._execute_run(request)
            self._status = EngineStatus.COMPLETED
            return response
        except Exception as exc:  # noqa: BLE001
            self._status = EngineStatus.FAILED
            return EngineRunResponse(
                session_id=request.session_id,
                status=EngineStatus.FAILED,
                summary="",
                errors=(
                    EngineError(
                        code="ENGINE_RUN_FAILED",
                        message=str(exc),
                    ),
                ),
            )

    def shutdown(self) -> None:
        """Shut down the engine and return to idle."""
        self._on_shutdown()
        self._status = EngineStatus.IDLE

    @property
    def configuration(self) -> EngineConfiguration:
        return self._configuration

    def _on_initialize(self) -> None:
        """Hook for subclasses to perform initialization work."""

    def _on_shutdown(self) -> None:
        """Hook for subclasses to perform shutdown work."""

    @abstractmethod
    def _execute_run(self, request: EngineRunRequest) -> EngineRunResponse:
        """Execute the engine run implementation."""
