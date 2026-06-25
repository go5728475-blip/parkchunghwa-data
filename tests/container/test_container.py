"""Tests for dependency injection container."""

from __future__ import annotations

import pytest

from core.container.container import Container
from core.container.errors import CircularDependencyError, ContainerError
from core.container.registration import ServiceLifetime


def test_container_register_and_resolve_singleton() -> None:
    container = Container()
    sentinel = object()
    container.register_singleton("service", sentinel)

    assert container.exists("service")
    assert container.resolve("service") is sentinel


def test_container_register_transient_returns_new_instances() -> None:
    container = Container()
    container.register("transient", list, lifetime=ServiceLifetime.TRANSIENT)

    first = container.resolve("transient")
    second = container.resolve("transient")

    assert first is not second
    assert first == []
    assert second == []


def test_container_register_singleton_factory_caches_instance() -> None:
    container = Container()
    calls = {"count": 0}

    def factory() -> str:
        calls["count"] += 1
        return "created"

    container.register("lazy", factory, lifetime=ServiceLifetime.SINGLETON)

    assert container.resolve("lazy") == "created"
    assert container.resolve("lazy") == "created"
    assert calls["count"] == 1


def test_container_factory_lazy_singleton_backward_compat() -> None:
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
    container.register("b", lambda: 2, lifetime=ServiceLifetime.TRANSIENT)

    container.remove("a")
    assert not container.exists("a")

    container.clear()
    assert not container.exists("b")


def test_container_resolve_missing_raises() -> None:
    container = Container()
    with pytest.raises(ContainerError, match="not registered"):
        container.resolve("missing")


def test_container_detects_circular_dependency() -> None:
    container = Container()

    def service_a() -> str:
        container.resolve("service_b")
        return "a"

    def service_b() -> str:
        container.resolve("service_a")
        return "b"

    container.register("service_a", service_a, lifetime=ServiceLifetime.SINGLETON)
    container.register("service_b", service_b, lifetime=ServiceLifetime.SINGLETON)

    with pytest.raises(CircularDependencyError, match="Circular dependency"):
        container.resolve("service_a")
