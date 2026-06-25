"""Tests for transaction context state."""

from __future__ import annotations

from core.uow.context import TransactionContext
from core.uow.support import mark_committed, mark_rolled_back, mark_started


def test_transaction_context_defaults() -> None:
    context = TransactionContext()

    assert context.active is False
    assert context.committed is False
    assert context.rolled_back is False
    assert context.started_at is None
    assert context.finished_at is None


def test_mark_started_sets_active_state() -> None:
    context = TransactionContext()

    mark_started(context)

    assert context.active is True
    assert context.committed is False
    assert context.rolled_back is False
    assert context.started_at is not None
    assert context.finished_at is None


def test_mark_committed_clears_active_state() -> None:
    context = TransactionContext()
    mark_started(context)

    mark_committed(context)

    assert context.active is False
    assert context.committed is True
    assert context.rolled_back is False
    assert context.finished_at is not None


def test_mark_rolled_back_clears_active_state() -> None:
    context = TransactionContext()
    mark_started(context)

    mark_rolled_back(context)

    assert context.active is False
    assert context.committed is False
    assert context.rolled_back is True
    assert context.finished_at is not None
