"""Canonical report models for the rendering layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from core.domain.ids import ReportId
from core.domain.models import TraceEntry
from core.domain.value_objects import ReportSection


@dataclass(frozen=True, kw_only=True)
class ReportTocEntry:
    """Single table-of-contents entry."""

    order: int
    title: str
    capability: str


@dataclass(frozen=True, kw_only=True)
class CapabilityReportGroup:
    """Capability-grouped report sections for multi-section rendering."""

    capability: str
    label: str
    sections: tuple[ReportSection, ...]


@dataclass(frozen=True, kw_only=True)
class BuiltReport:
    """Canonical report produced by ReportBuilder for UI/API/CLI rendering."""

    report_id: ReportId
    title: str
    summary: str
    sections: tuple[ReportSection, ...]
    toc: tuple[ReportTocEntry, ...]
    generated_at: str
    capability_groups: tuple[CapabilityReportGroup, ...]
    trace: tuple[TraceEntry, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if self.trace is None:
            object.__setattr__(self, "trace", ())
