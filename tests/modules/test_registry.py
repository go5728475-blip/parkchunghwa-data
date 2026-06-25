"""Tests for module registry."""

from __future__ import annotations

import pytest

from core.container.container import Container
from core.modules.builtin.wealth_module import WealthModule
from core.modules.interfaces import IModule
from core.modules.registry import ModuleRegistry, ModuleRegistryError


class _StubModule(IModule):
    def __init__(self, name: str) -> None:
        self._name = name
        self.booted = False
        self.shutdown_called = False

    def name(self) -> str:
        return self._name

    def version(self) -> str:
        return "1.0.0"

    def capabilities(self) -> tuple[str, ...]:
        return (f"{self._name}.analysis",)

    def register(self, container: Container) -> None:
        container.register_singleton(f"module.{self._name}", self)

    def boot(self, container: Container) -> None:
        self.booted = True

    def shutdown(self, container: Container) -> None:
        self.shutdown_called = True
        self.booted = False


def test_registry_register_resolve_and_list() -> None:
    registry = ModuleRegistry()
    module = _StubModule("wealth")
    registry.register(module)

    assert registry.exists("wealth")
    assert registry.resolve("wealth") is module
    assert registry.list() == ("wealth",)


def test_registry_unregister() -> None:
    registry = ModuleRegistry()
    registry.register(_StubModule("career"))

    registry.unregister("career")

    assert not registry.exists("career")


def test_registry_duplicate_register_raises() -> None:
    registry = ModuleRegistry()
    registry.register(_StubModule("wealth"))

    with pytest.raises(ModuleRegistryError, match="already registered"):
        registry.register(_StubModule("wealth"))


def test_registry_boot_and_shutdown_all() -> None:
    registry = ModuleRegistry()
    first = _StubModule("wealth")
    second = _StubModule("career")
    registry.register(first)
    registry.register(second)
    container = Container()

    registry.register_all(container)
    registry.boot_all(container)

    assert registry.is_booted("wealth")
    assert registry.is_booted("career")
    assert first.booted
    assert second.booted

    registry.shutdown_all(container)

    assert not registry.is_booted("wealth")
    assert first.shutdown_called


def test_registry_boot_and_shutdown_single_module() -> None:
    registry = ModuleRegistry()
    registry.register(WealthModule())
    container = Container()
    registry.register_all(container)

    registry.boot_module("wealth", container)
    assert registry.is_booted("wealth")

    registry.shutdown_module("wealth", container)
    assert not registry.is_booted("wealth")


def test_registry_descriptor_reports_loaded_state() -> None:
    registry = ModuleRegistry()
    registry.register(WealthModule())
    container = Container()
    registry.register_all(container)
    registry.boot_all(container)

    descriptor = registry.descriptor("wealth")

    assert descriptor.name == "wealth"
    assert descriptor.version == "0.1.0"
    assert descriptor.capabilities == ("wealth.analysis",)
    assert descriptor.loaded is True
