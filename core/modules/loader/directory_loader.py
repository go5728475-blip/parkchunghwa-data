"""Directory-based module package loader."""

from __future__ import annotations

import importlib.util
from dataclasses import dataclass
from pathlib import Path

from typing import Any

from core.modules.interfaces import IModule
from core.modules.loader.errors import ModuleLoaderError
from core.modules.loader.interfaces import IModuleLoader
from core.modules.manifest import ModuleManifest, load_manifest

MODULE_FILENAME = "module.py"


@dataclass(frozen=True, kw_only=True)
class _LoadedPackage:
    path: str
    module: Any


class DirectoryModuleLoader(IModuleLoader):
    """Loads engine modules from Python package directories."""

    def __init__(self) -> None:
        self._loaded: dict[str, _LoadedPackage] = {}

    def load(self, path: str) -> IModule:
        package_dir = Path(path).resolve()
        if not self.supports(str(package_dir)):
            msg = f"Unsupported directory module package: {package_dir}"
            raise ModuleLoaderError(msg)

        manifest = load_manifest(package_dir)
        if manifest.name in self._loaded:
            msg = f"Module already loaded: {manifest.name}"
            raise ModuleLoaderError(msg)

        module = self._instantiate_module(package_dir, manifest)
        self._validate_module(module, manifest)
        self._loaded[manifest.name] = _LoadedPackage(
            path=str(package_dir),
            module=module,
        )
        return module

    def unload(self, module_name: str) -> None:
        if module_name not in self._loaded:
            msg = f"Module not loaded: {module_name}"
            raise ModuleLoaderError(msg)
        self._loaded.pop(module_name)

    def reload(self, module_name: str) -> IModule:
        record = self._loaded.get(module_name)
        if record is None:
            msg = f"Module not loaded: {module_name}"
            raise ModuleLoaderError(msg)
        package_path = record.path
        self.unload(module_name)
        return self.load(package_path)

    def list_loaded(self) -> tuple[str, ...]:
        return tuple(sorted(self._loaded))

    def supports(self, path: str) -> bool:
        package_dir = Path(path)
        if not package_dir.is_dir():
            return False
        return (package_dir / MODULE_FILENAME).is_file() and (
            package_dir / "manifest.json"
        ).is_file()

    def package_path(self, module_name: str) -> str | None:
        record = self._loaded.get(module_name)
        if record is None:
            return None
        return record.path

    def _instantiate_module(
        self,
        package_dir: Path,
        manifest: ModuleManifest,
    ) -> IModule:
        module_path = package_dir / MODULE_FILENAME
        module_name = f"dynamic_module_{manifest.name}"
        spec = importlib.util.spec_from_file_location(module_name, module_path)
        if spec is None or spec.loader is None:
            msg = f"Unable to load module file: {module_path}"
            raise ModuleLoaderError(msg)

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        try:
            module_class = getattr(module, manifest.module_class)
        except AttributeError as exc:
            msg = (
                f"Module class '{manifest.module_class}' not found in "
                f"{module_path}"
            )
            raise ModuleLoaderError(msg) from exc

        try:
            instance = module_class()
        except TypeError as exc:
            msg = f"Module class '{manifest.module_class}' must be instantiable."
            raise ModuleLoaderError(msg) from exc

        return instance

    @staticmethod
    def _validate_module(module: object, manifest: ModuleManifest) -> None:
        if not _implements_module_contract(module):
            msg = (
                f"Module '{manifest.module_class}' must implement the module contract "
                f"for package '{manifest.name}'."
            )
            raise ModuleLoaderError(msg)

        if module.name() != manifest.name:
            msg = (
                f"Module name mismatch: manifest={manifest.name}, "
                f"module={module.name()}"
            )
            raise ModuleLoaderError(msg)

        if module.version() != manifest.version:
            msg = (
                f"Module version mismatch: manifest={manifest.version}, "
                f"module={module.version()}"
            )
            raise ModuleLoaderError(msg)

        if tuple(module.capabilities()) != manifest.capabilities:
            msg = (
                f"Module capabilities mismatch for '{manifest.name}'."
            )
            raise ModuleLoaderError(msg)


def _implements_module_contract(module: object) -> bool:
    required = ("name", "version", "capabilities", "register", "boot", "shutdown")
    return all(callable(getattr(module, attribute, None)) for attribute in required)
