"""Correlation context for metrics and trace alignment."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime


@dataclass(frozen=True, kw_only=True)
class CorrelationContext:
    """Shared correlation metadata across metrics and trace entries."""

    correlation_id: str
    workflow_id: str | None = None
    transaction_id: str | None = None
    started_at: str | None = None


_current_context: CorrelationContext | None = None


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def get_correlation_context() -> CorrelationContext | None:
    """Return the active correlation context."""
    return _current_context


def get_correlation_id() -> str | None:
    """Return the active correlation id when set."""
    if _current_context is None:
        return None
    return _current_context.correlation_id


def set_correlation_context(context: CorrelationContext | None) -> None:
    """Set or clear the active correlation context."""
    global _current_context
    _current_context = context


def update_correlation_context(**changes: str | None) -> None:
    """Update fields on the active correlation context."""
    global _current_context
    if _current_context is None:
        return
    _current_context = replace(_current_context, **changes)


def clear_correlation_context() -> None:
    """Clear the active correlation context."""
    set_correlation_context(None)
