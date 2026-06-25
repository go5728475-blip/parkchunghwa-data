"""Engine interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from core.contracts.explanation import Explanation


class IEngine(ABC):
    """Core orchestration port for explainable engine execution."""

    @abstractmethod
    async def execute(self, operation: str, context: dict[str, Any]) -> dict[str, Any]:
        """Execute an engine operation with the given context."""

    @abstractmethod
    async def explain(self, operation: str, context: dict[str, Any]) -> Explanation:
        """Produce an explainable trace for the given operation."""
