"""Tests for dependency injection container."""

from __future__ import annotations

import pytest

from core.bootstrap.container import Container, ContainerError


def test_container_singleton_registration_and_resolution() -> None:
    container = Container()
    sentinel = object()
    container.register_singleton("service", sentinel)

    assert container.exists("service")
    assert container.resolve("service") is sentinel


def test_container_factory_lazy_singleton() -> None:
    container = Container()
    calls = {"count": 0}

    def factory() -> str:
        calls["count"] += 1
        return "created"

    container.register_factory("lazy", factory)
    assert container.resolve("lazy") == "created"
    assert container.resolve("lazy") == "created"
    assert calls["count"] == 1


def test_container_override() -> None:
    container = Container()
    container.register_singleton("value", "original")
    container.override("value", "overridden")

    assert container.resolve("value") == "overridden"


def test_container_remove_and_clear() -> None:
    container = Container()
    container.register_singleton("a", 1)
    container.register_factory("b", lambda: 2)

    container.remove("a")
    assert not container.exists("a")

    container.clear()
    assert not container.exists("b")


def test_container_resolve_missing_raises() -> None:
    container = Container()
    with pytest.raises(ContainerError, match="not registered"):
        container.resolve("missing")
