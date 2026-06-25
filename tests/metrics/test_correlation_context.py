"""Tests for correlation context."""

from __future__ import annotations

from core.metrics.context import (
    CorrelationContext,
    clear_correlation_context,
    get_correlation_context,
    get_correlation_id,
    set_correlation_context,
    update_correlation_context,
)


def setup_function() -> None:
    clear_correlation_context()


def teardown_function() -> None:
    clear_correlation_context()


def test_correlation_context_fields() -> None:
    context = CorrelationContext(
        correlation_id="corr-1",
        workflow_id="workflow-1",
        transaction_id="txn-1",
        started_at="2026-06-18T00:00:00+00:00",
    )

    assert context.correlation_id == "corr-1"
    assert context.workflow_id == "workflow-1"
    assert context.transaction_id == "txn-1"
    assert context.started_at == "2026-06-18T00:00:00+00:00"


def test_set_and_get_correlation_context() -> None:
    context = CorrelationContext(correlation_id="corr-2")
    set_correlation_context(context)

    assert get_correlation_context() == context
    assert get_correlation_id() == "corr-2"


def test_update_correlation_context() -> None:
    set_correlation_context(CorrelationContext(correlation_id="corr-3"))

    update_correlation_context(
        workflow_id="workflow-3",
        transaction_id="txn-3",
    )

    context = get_correlation_context()
    assert context is not None
    assert context.correlation_id == "corr-3"
    assert context.workflow_id == "workflow-3"
    assert context.transaction_id == "txn-3"


def test_clear_correlation_context() -> None:
    set_correlation_context(CorrelationContext(correlation_id="corr-4"))

    clear_correlation_context()

    assert get_correlation_context() is None
    assert get_correlation_id() is None
