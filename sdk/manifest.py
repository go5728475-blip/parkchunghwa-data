"""Plugin package manifest model."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True, kw_only=True)
class PluginManifest:
    """Describes a MASTER ENGINE plugin package."""

    name: str
    version: str
    author: str
    description: str
    capabilities: tuple[str, ...]
    module_class: str
    sdk_version: str | None = None


def load_manifest(path: Path | str) -> PluginManifest:
    """Load a manifest from a plugin directory or manifest file path."""
    manifest_path = _resolve_manifest_path(path)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        msg = "Manifest must be a JSON object."
        raise ValueError(msg)
    return PluginManifest(
        name=str(payload["name"]).strip(),
        version=str(payload["version"]).strip(),
        author=str(payload["author"]).strip(),
        description=str(payload["description"]).strip(),
        capabilities=tuple(str(item).strip() for item in payload["capabilities"]),
        module_class=str(payload["module_class"]).strip(),
        sdk_version=(
            str(payload["sdk_version"]).strip()
            if payload.get("sdk_version") is not None
            else None
        ),
    )


def _resolve_manifest_path(path: Path | str) -> Path:
    candidate = Path(path)
    if candidate.is_dir():
        return candidate / MANIFEST_FILENAME
    return candidate
