"""Tests for module loader manager."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.container.container import Container
from core.modules.loader.manager import LoaderManager, LoaderManagerError
from core.modules.loader.stubs import WhlModuleLoader, ZipModuleLoader
from core.modules.registry import ModuleRegistry
from core.bootstrap.factory import ApplicationFactory


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"
STUDY_PLUGIN_DIR = FIXTURES_DIR / "study_plugin"


def _manager() -> LoaderManager:
    factory = ApplicationFactory()
    return factory.create_loader_manager(ModuleRegistry(), Container())


def test_loader_manager_resolves_directory_loader() -> None:
    manager = _manager()

    loader = manager.resolve_loader(str(HEALTH_PLUGIN_DIR))

    assert loader.supports(str(HEALTH_PLUGIN_DIR))


def test_loader_manager_registers_zip_and_whl_stubs() -> None:
    manager = _manager()

    assert manager.resolve_loader("package.zip").supports("package.zip")
    assert manager.resolve_loader("package.whl").supports("package.whl")


def test_zip_loader_is_not_implemented() -> None:
    loader = ZipModuleLoader()

    with pytest.raises(Exception, match="not implemented"):
        loader.load("package.zip")


def test_loader_manager_load_registers_and_boots_module() -> None:
    registry = ModuleRegistry()
    container = Container()
    manager = ApplicationFactory().create_loader_manager(registry, container)

    module_name = manager.load(str(HEALTH_PLUGIN_DIR))

    assert module_name == "health"
    assert registry.exists("health")
    assert registry.is_booted("health")
    assert manager.list_loaded() == ("health",)


def test_loader_manager_unload_removes_dynamic_module() -> None:
    registry = ModuleRegistry()
    container = Container()
    manager = ApplicationFactory().create_loader_manager(registry, container)
    manager.load(str(HEALTH_PLUGIN_DIR))

    manager.unload("health")

    assert not registry.exists("health")
    assert manager.list_loaded() == ()


def test_loader_manager_reload_dynamic_module() -> None:
    registry = ModuleRegistry()
    container = Container()
    manager = ApplicationFactory().create_loader_manager(registry, container)
    manager.load(str(STUDY_PLUGIN_DIR))

    reloaded = manager.reload("study")

    assert reloaded == "study"
    assert registry.exists("study")
    assert registry.is_booted("study")


def test_loader_manager_rejects_unknown_path() -> None:
    manager = _manager()

    with pytest.raises(LoaderManagerError, match="No loader supports"):
        manager.load("/missing/package")
