"""Tests for directory module loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.modules.loader.directory_loader import DirectoryModuleLoader
from core.modules.loader.errors import ModuleLoaderError
from core.modules.manifest import load_manifest


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


def test_directory_loader_supports_package_directory() -> None:
    loader = DirectoryModuleLoader()

    assert loader.supports(str(HEALTH_PLUGIN_DIR)) is True
    assert loader.supports(str(FIXTURES_DIR)) is False
    assert loader.supports("missing.zip") is False


def test_load_manifest_reads_package_metadata() -> None:
    manifest = load_manifest(HEALTH_PLUGIN_DIR)

    assert manifest.name == "health"
    assert manifest.version == "1.0.0"
    assert manifest.author == "MASTER ENGINE"
    assert manifest.capabilities == ("health.analysis",)
    assert manifest.module_class == "Module"


def test_directory_loader_loads_module_instance() -> None:
    loader = DirectoryModuleLoader()

    module = loader.load(str(HEALTH_PLUGIN_DIR))

    assert module.name() == "health"
    assert module.version() == "1.0.0"
    assert module.capabilities() == ("health.analysis",)
    assert loader.list_loaded() == ("health",)


def test_directory_loader_reload_replaces_module() -> None:
    loader = DirectoryModuleLoader()
    loader.load(str(HEALTH_PLUGIN_DIR))

    reloaded = loader.reload("health")

    assert reloaded.name() == "health"
    assert loader.list_loaded() == ("health",)


def test_directory_loader_unload_removes_module() -> None:
    loader = DirectoryModuleLoader()
    loader.load(str(HEALTH_PLUGIN_DIR))

    loader.unload("health")

    assert loader.list_loaded() == ()


def test_directory_loader_rejects_invalid_module_class(tmp_path: Path) -> None:
    package_dir = tmp_path / "invalid_plugin"
    package_dir.mkdir()
    (package_dir / "manifest.json").write_text(
        """
        {
          "name": "invalid",
          "version": "1.0.0",
          "author": "test",
          "description": "invalid",
          "capabilities": ["invalid.analysis"],
          "module_class": "MissingClass"
        }
        """.strip(),
        encoding="utf-8",
    )
    (package_dir / "module.py").write_text(
        "class Module:\n    pass\n",
        encoding="utf-8",
    )

    loader = DirectoryModuleLoader()

    with pytest.raises(ModuleLoaderError, match="not found"):
        loader.load(str(package_dir))
