"""Plugin package validation."""

from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path
from typing import Any

from sdk.manifest import MANIFEST_FILENAME, PluginManifest, load_manifest
from sdk.module import IModule
from sdk.version import PLUGIN_SDK_VERSION

MODULE_FILENAME = "module.py"
_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")
_CAPABILITY_PATTERN = re.compile(r"^[a-z][a-z0-9_.]*$")


class ValidationError(Exception):
    """Raised when plugin package validation fails."""


def validate_manifest(payload: dict[str, Any]) -> PluginManifest:
    """Validate manifest fields and return a PluginManifest."""
    required = ("name", "version", "author", "description", "capabilities", "module_class")
    for field in required:
        if field not in payload:
            msg = f"Manifest missing required field: {field}"
            raise ValidationError(msg)

    name = _require_non_empty_string(payload["name"], "name")
    version = _require_non_empty_string(payload["version"], "version")
    author = _require_non_empty_string(payload["author"], "author")
    description = _require_non_empty_string(payload["description"], "description")
    module_class = _require_non_empty_string(payload["module_class"], "module_class")

    if not _NAME_PATTERN.match(name):
        msg = f"Invalid module name: {name}"
        raise ValidationError(msg)
    if not _VERSION_PATTERN.match(version):
        msg = f"Invalid semantic version: {version}"
        raise ValidationError(msg)

    capabilities = payload["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        msg = "Manifest capabilities must be a non-empty list."
        raise ValidationError(msg)

    normalized_capabilities: list[str] = []
    for capability in capabilities:
        value = _require_non_empty_string(capability, "capabilities")
        if not _CAPABILITY_PATTERN.match(value):
            msg = f"Invalid capability name: {value}"
            raise ValidationError(msg)
        normalized_capabilities.append(value)

    sdk_version = payload.get("sdk_version")
    normalized_sdk_version = None
    if sdk_version is not None:
        normalized_sdk_version = _require_non_empty_string(sdk_version, "sdk_version")
        validate_sdk_compatibility(normalized_sdk_version)

    return PluginManifest(
        name=name,
        version=version,
        author=author,
        description=description,
        capabilities=tuple(normalized_capabilities),
        module_class=module_class,
        sdk_version=normalized_sdk_version,
    )


def validate_manifest_file(path: Path | str) -> PluginManifest:
    """Validate a manifest.json file."""
    manifest_path = Path(path)
    if manifest_path.is_dir():
        manifest_path = manifest_path / MANIFEST_FILENAME
    if not manifest_path.is_file():
        msg = f"Manifest not found: {manifest_path}"
        raise ValidationError(msg)

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Invalid manifest JSON: {manifest_path}"
        raise ValidationError(msg) from exc

    if not isinstance(payload, dict):
        msg = "Manifest must be a JSON object."
        raise ValidationError(msg)

    return validate_manifest(payload)


def validate_plugin_package(path: Path | str) -> PluginManifest:
    """Validate a plugin package directory structure and module class."""
    package_dir = Path(path).resolve()
    if not package_dir.is_dir():
        msg = f"Plugin package directory not found: {package_dir}"
        raise ValidationError(msg)

    manifest = validate_manifest_file(package_dir)
    module_path = package_dir / MODULE_FILENAME
    if not module_path.is_file():
        msg = f"Module file not found: {module_path}"
        raise ValidationError(msg)

    module = _load_module_class(package_dir, manifest.module_class)
    if not isinstance(module, IModule):
        msg = f"Module class '{manifest.module_class}' must implement sdk.IModule."
        raise ValidationError(msg)

    if module.name() != manifest.name:
        msg = (
            f"Module name mismatch: manifest={manifest.name}, "
            f"module={module.name()}"
        )
        raise ValidationError(msg)
    if module.version() != manifest.version:
        msg = (
            f"Module version mismatch: manifest={manifest.version}, "
            f"module={module.version()}"
        )
        raise ValidationError(msg)
    if tuple(module.capabilities()) != manifest.capabilities:
        msg = f"Module capabilities mismatch for '{manifest.name}'."
        raise ValidationError(msg)

    return manifest


def validate_sdk_compatibility(sdk_version: str) -> None:
    """Ensure manifest sdk_version is compatible with PLUGIN_SDK_VERSION."""
    if not _VERSION_PATTERN.match(sdk_version):
        msg = f"Invalid sdk_version: {sdk_version}"
        raise ValidationError(msg)

    manifest_major, manifest_minor, _ = sdk_version.split(".")
    sdk_major, sdk_minor, _ = PLUGIN_SDK_VERSION.split(".")
    if (manifest_major, manifest_minor) != (sdk_major, sdk_minor):
        msg = (
            f"Incompatible sdk_version {sdk_version}; "
            f"expected {sdk_major}.{sdk_minor}.x"
        )
        raise ValidationError(msg)


def _load_module_class(package_dir: Path, module_class_name: str) -> IModule:
    module_path = package_dir / MODULE_FILENAME
    module_name = f"sdk_validation_{package_dir.name}"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec is None or spec.loader is None:
        msg = f"Unable to load module file: {module_path}"
        raise ValidationError(msg)

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    try:
        module_class = getattr(module, module_class_name)
    except AttributeError as exc:
        msg = f"Module class '{module_class_name}' not found in {module_path}"
        raise ValidationError(msg) from exc

    try:
        instance = module_class()
    except TypeError as exc:
        msg = f"Module class '{module_class_name}' must be instantiable."
        raise ValidationError(msg) from exc

    return instance


def _require_non_empty_string(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        msg = f"Manifest field '{field_name}' must be a non-empty string."
        raise ValidationError(msg)
    return value.strip()
