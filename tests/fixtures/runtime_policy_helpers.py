"""Shared runtime policy fixtures for plugin tests."""

from __future__ import annotations

import json
from pathlib import Path

RUNTIME_POLICY = {
    "version": "1.0",
    "id": "fixture-runtime-policy",
    "name": "Fixture Runtime Policy",
    "rules": [
        {
            "id": "require-manifest",
            "severity": "fail",
            "actions": ["block_load"],
            "field": "manifest",
            "required": True,
        },
        {
            "id": "warn-provider",
            "severity": "warn",
            "actions": ["warn"],
            "field": "source",
            "forbidden": "openai",
        },
    ],
}


def write_runtime_policy(directory: Path) -> Path:
    path = directory / "runtime_policy.json"
    path.write_text(json.dumps(RUNTIME_POLICY, indent=2), encoding="utf-8")
    return path


def write_plugin_package(
    directory: Path,
    *,
    name: str,
    version: str = "1.0.0",
    sdk_version: str = "1.0.0",
    source: str | None = None,
    certification_policy: str | None = None,
) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, object] = {
        "name": name,
        "version": version,
        "author": "MASTER ENGINE",
        "description": f"{name} fixture plugin",
        "capabilities": [f"{name}.analysis"],
        "module_class": "Module",
        "sdk_version": sdk_version,
    }
    if certification_policy:
        manifest["certification"] = {"policy": certification_policy}
    (directory / "manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )
    module_source = source or f'''
from sdk import BaseModule


class Module(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            name="{name}",
            version="{version}",
            capabilities=("{name}.analysis",),
        )
'''
    (directory / "module.py").write_text(module_source.strip() + "\n", encoding="utf-8")
    (directory / "__init__.py").write_text("", encoding="utf-8")
    return directory
