"""Tests for service lifetimes."""

from __future__ import annotations

import pytest

from core.container.container import Container
from core.container.errors import ContainerError
from core.container.registration import ServiceLifetime


class _Counter:
    def __init__(self) -> None:
        self.value = 0


def _increment(counter: _Counter) -> int:
    counter.value += 1
    return counter.value


def test_singleton_lifetime_reuses_instance() -> None:
    container = Container()
    counter = _Counter()
    container.register(
        "counter",
        lambda: _increment(counter),
        lifetime=ServiceLifetime.SINGLETON,
    )

    assert container.resolve("counter") == 1
    assert container.resolve("counter") == 1
    assert counter.value == 1


def test_transient_lifetime_creates_new_instances() -> None:
    container = Container()
    counter = _Counter()
    container.register(
        "counter",
        lambda: _increment(counter),
        lifetime=ServiceLifetime.TRANSIENT,
    )

    assert container.resolve("counter") == 1
    assert container.resolve("counter") == 2
    assert counter.value == 2


def test_scoped_lifetime_is_reserved() -> None:
    container = Container()

    with pytest.raises(ContainerError, match="Scoped lifetime"):
        container.register("scoped", lambda: object(), lifetime=ServiceLifetime.SCOPED)
