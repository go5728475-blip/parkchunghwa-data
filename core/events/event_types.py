"""Typed domain events for workflow, analysis, report, and export."""

from __future__ import annotations

from dataclasses import dataclass

from core.events.models import DomainEvent


@dataclass(frozen=True, kw_only=True)
class WorkflowStarted(DomainEvent):
    """Raised when a workflow execution begins."""


@dataclass(frozen=True, kw_only=True)
class WorkflowCompleted(DomainEvent):
    """Raised when a workflow execution completes."""


@dataclass(frozen=True, kw_only=True)
class AnalysisStarted(DomainEvent):
    """Raised when an analysis run begins."""


@dataclass(frozen=True, kw_only=True)
class AnalysisCompleted(DomainEvent):
    """Raised when an analysis run completes."""


@dataclass(frozen=True, kw_only=True)
class ReportBuilt(DomainEvent):
    """Raised when a built report is produced."""


@dataclass(frozen=True, kw_only=True)
class ReportExported(DomainEvent):
    """Raised when a built report is exported."""


@dataclass(frozen=True, kw_only=True)
class ProviderCalled(DomainEvent):
    """Raised when a provider is invoked for enrichment."""


@dataclass(frozen=True, kw_only=True)
class ProviderCompleted(DomainEvent):
    """Raised when provider enrichment completes."""


@dataclass(frozen=True, kw_only=True)
class CapabilityExecuted(DomainEvent):
    """Raised when a capability plugin execution completes."""


@dataclass(frozen=True, kw_only=True)
class TransactionStarted(DomainEvent):
    """Raised when a workflow transaction begins."""


@dataclass(frozen=True, kw_only=True)
class TransactionCommitted(DomainEvent):
    """Raised when a workflow transaction commits."""


@dataclass(frozen=True, kw_only=True)
class TransactionRolledBack(DomainEvent):
    """Raised when a workflow transaction rolls back."""
