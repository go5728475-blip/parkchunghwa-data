"""Tests for dynamic module integration."""

from __future__ import annotations

from pathlib import Path

from core.bootstrap.bootstrap import Bootstrap
from core.bootstrap.factory import ApplicationFactory
from core.container.container import Container
from core.modules.loader.directory_loader import DirectoryModuleLoader
from core.modules.registry import ModuleRegistry


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


def test_dynamic_module_coexists_with_builtin_modules() -> None:
    bootstrap = Bootstrap().build()
    manager = bootstrap.loader_manager()

    manager.load(str(HEALTH_PLUGIN_DIR))

    registry = bootstrap.module_registry()
    assert registry.exists("wealth")
    assert registry.exists("health")
    assert registry.is_booted("health")


def test_factory_creates_module_loader_and_manager() -> None:
    factory = ApplicationFactory()

    assert isinstance(factory.create_module_loader(), DirectoryModuleLoader)
    manager = factory.create_loader_manager(ModuleRegistry(), Container())
    assert manager.resolve_loader(str(HEALTH_PLUGIN_DIR)).supports(str(HEALTH_PLUGIN_DIR))


def test_bootstrap_exposes_loader_manager() -> None:
    bootstrap = Bootstrap().build()

    assert bootstrap.container().exists("loader_manager")
    assert bootstrap.loader_manager() is not None
