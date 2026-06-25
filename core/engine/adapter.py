"""Engine adapter for application layer integration."""

from __future__ import annotations

from core.engine.kernel import EngineKernel
from core.engine.lifecycle import EngineLifecycleManager
from core.engine.request import EngineRunRequest
from core.engine.response import EngineRunResponse


class EngineAdapter:
    """Wraps an engine kernel for application-layer invocation."""

    def __init__(
        self,
        engine: EngineKernel,
        lifecycle_manager: EngineLifecycleManager,
    ) -> None:
        self._engine = engine
        self._lifecycle_manager = lifecycle_manager

    @property
    def engine(self) -> EngineKernel:
        return self._engine

    @property
    def lifecycle_manager(self) -> EngineLifecycleManager:
        return self._lifecycle_manager

    def run_analysis(self, request: EngineRunRequest) -> EngineRunResponse:
        """Run analysis with lifecycle preparation for consecutive runs."""
        return self._lifecycle_manager.run_with_lifecycle(request)
