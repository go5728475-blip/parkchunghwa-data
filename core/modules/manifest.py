"""Module package manifest."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


class ModuleManifestError(Exception):
    """Raised when a module manifest cannot be read or validated."""


MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True, kw_only=True)
class ModuleManifest:
    """Describes a loadable engine module package."""

    name: str
    version: str
    author: str
    description: str
    capabilities: tuple[str, ...]
    module_class: str


def load_manifest(package_dir: Path) -> ModuleManifest:
    """Read and validate a module manifest from a package directory."""
    manifest_path = package_dir / MANIFEST_FILENAME
    if not manifest_path.is_file():
        msg = f"Manifest not found: {manifest_path}"
        raise ModuleManifestError(msg)

    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Invalid manifest JSON: {manifest_path}"
        raise ModuleManifestError(msg) from exc

    if not isinstance(payload, dict):
        msg = f"Manifest must be a JSON object: {manifest_path}"
        raise ModuleManifestError(msg)

    return _manifest_from_dict(payload, manifest_path)


def _manifest_from_dict(payload: dict[str, object], manifest_path: Path) -> ModuleManifest:
    required = ("name", "version", "author", "description", "capabilities", "module_class")
    for field in required:
        if field not in payload:
            msg = f"Manifest missing '{field}': {manifest_path}"
            raise ModuleManifestError(msg)

    capabilities = payload["capabilities"]
    if not isinstance(capabilities, list) or not capabilities:
        msg = f"Manifest capabilities must be a non-empty list: {manifest_path}"
        raise ModuleManifestError(msg)
    if any(not isinstance(item, str) or not item.strip() for item in capabilities):
        msg = f"Manifest capabilities must be non-empty strings: {manifest_path}"
        raise ModuleManifestError(msg)

    for field in ("name", "version", "author", "description", "module_class"):
        value = payload[field]
        if not isinstance(value, str) or not value.strip():
            msg = f"Manifest field '{field}' must be a non-empty string: {manifest_path}"
            raise ModuleManifestError(msg)

    return ModuleManifest(
        name=str(payload["name"]).strip(),
        version=str(payload["version"]).strip(),
        author=str(payload["author"]).strip(),
        description=str(payload["description"]).strip(),
        capabilities=tuple(str(item).strip() for item in capabilities),
        module_class=str(payload["module_class"]).strip(),
    )
