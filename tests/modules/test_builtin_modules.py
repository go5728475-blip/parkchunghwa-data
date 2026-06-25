"""Tests for builtin engine modules."""

from __future__ import annotations

from core.container.container import Container
from core.modules.builtin import create_builtin_modules
from core.modules.builtin.career_module import CareerModule
from core.modules.builtin.master_lock_module import MasterLockModule
from core.modules.builtin.relationship_module import RelationshipModule
from core.modules.builtin.wealth_module import WealthModule
from core.modules.models import ModuleDescriptor
from core.modules.registry import ModuleRegistry


def test_create_builtin_modules_includes_four_engines() -> None:
    modules = create_builtin_modules()

    names = {module.name() for module in modules}
    assert names == {"master_lock", "wealth", "career", "relationship"}


def test_builtin_module_register_boot_shutdown_lifecycle() -> None:
    module = WealthModule()
    container = Container()

    module.register(container)
    descriptor = container.resolve("module.wealth")
    assert isinstance(descriptor, ModuleDescriptor)
    assert descriptor.loaded is False

    module.boot(container)
    descriptor = container.resolve("module.wealth")
    assert descriptor.loaded is True

    module.shutdown(container)
    descriptor = container.resolve("module.wealth")
    assert descriptor.loaded is False


def test_builtin_modules_register_in_registry() -> None:
    registry = ModuleRegistry()
    for module in create_builtin_modules():
        registry.register(module)

    assert registry.exists("master_lock")
    assert registry.exists("wealth")
    assert registry.exists("career")
    assert registry.exists("relationship")


def test_master_lock_module_capabilities() -> None:
    module = MasterLockModule()

    assert module.name() == "master_lock"
    assert module.capabilities() == ("master_lock.analysis",)


def test_career_and_relationship_module_versions() -> None:
    career = CareerModule()
    relationship = RelationshipModule()

    assert career.version() == "0.1.0"
    assert relationship.version() == "0.1.0"
