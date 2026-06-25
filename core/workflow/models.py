"""Workflow domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from core.contracts.metadata import Metadata
from core.domain.ids import ProviderId, SessionId, UserId, WorkflowId
from core.domain.models import AnalysisResult, TraceEntry
from core.domain.value_objects import BirthData


class ExecutionMode(StrEnum):
    """Workflow execution strategy."""

    SEQUENTIAL = "SEQUENTIAL"
    PARALLEL = "PARALLEL"


@dataclass(frozen=True, kw_only=True)
class Workflow:
    """Multi-capability analysis workflow definition."""

    workflow_id: WorkflowId
    name: str
    capabilities: tuple[str, ...]
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL

    def __post_init__(self) -> None:
        if not self.name.strip():
            msg = "Workflow name cannot be empty."
            raise ValueError(msg)
        if not self.capabilities:
            msg = "Workflow requires at least one capability."
            raise ValueError(msg)
        if any(not capability.strip() for capability in self.capabilities):
            msg = "Workflow capabilities cannot be blank."
            raise ValueError(msg)


@dataclass(frozen=True, kw_only=True)
class WorkflowRunContext:
    """Execution context shared across workflow capability runs."""

    metadata: Metadata
    session_id: SessionId
    user_id: UserId
    birth_data: BirthData


@dataclass(frozen=True, kw_only=True)
class WorkflowResult:
    """Aggregated output from a workflow execution."""

    workflow_id: WorkflowId
    analysis_results: tuple[AnalysisResult, ...]
    trace: tuple[TraceEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.trace is None:
            object.__setattr__(self, "trace", ())
