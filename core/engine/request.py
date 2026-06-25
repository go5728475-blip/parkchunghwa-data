"""Engine run request model."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.domain.ids import ProviderId, SessionId, UserId
from core.domain.models import AnalysisResult
from core.domain.value_objects import BirthData, EngineContext


@dataclass(frozen=True, kw_only=True)
class EngineRunRequest:
    """Input payload for a single engine run."""

    session_id: SessionId
    user_id: UserId
    birth_data: BirthData
    context: EngineContext
    capability: str = "stub.analysis"
    provider_id: ProviderId | None = None
    analysis_result: AnalysisResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.metadata is None:
            object.__setattr__(self, "metadata", {})
