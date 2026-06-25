"""Helpers for loading plugins into certification."""

from __future__ import annotations

from sdk.manifest import load_manifest

from core.modules.loader.directory_loader import DirectoryModuleLoader
from core.modules.loader.errors import ModuleLoaderError


class CertificationLoadError(Exception):
    """Raised when a plugin cannot be loaded for certification."""


def load_plugin_for_certification(path: str) -> tuple[object, DirectoryModuleLoader]:
    """Load a directory plugin package and attach manifest metadata."""
    loader = DirectoryModuleLoader()
    if not loader.supports(path):
        msg = f"Unsupported plugin package path: {path}"
        raise CertificationLoadError(msg)

    try:
        module = loader.load(path)
        manifest = load_manifest(path)
    except (ModuleLoaderError, ValueError, OSError) as exc:
        msg = f"Unable to load plugin package: {exc}"
        raise CertificationLoadError(msg) from exc

    module.manifest = manifest
    return module, loader
