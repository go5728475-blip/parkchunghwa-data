"""Engine run response model."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.domain.ids import ReportId, SessionId
from core.domain.models import AnalysisResult
from core.domain.value_objects import ExplanationTrace
from core.engine.errors import EngineError
from core.engine.status import EngineStatus


@dataclass(frozen=True, kw_only=True)
class EngineRunResponse:
    """Output payload from an engine run."""

    session_id: SessionId
    status: EngineStatus
    summary: str
    report_id: ReportId | None = None
    explanation_trace: ExplanationTrace | None = None
    analysis_result: AnalysisResult | None = None
    errors: tuple[EngineError, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.errors is None:
            object.__setattr__(self, "errors", ())
