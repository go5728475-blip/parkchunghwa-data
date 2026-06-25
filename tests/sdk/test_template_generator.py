"""Tests for SDK template generator."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from sdk.templates import create_plugin_template
from sdk.validation import validate_plugin_package
from sdk.version import PLUGIN_SDK_VERSION


def test_create_plugin_template_generates_package_structure(tmp_path: Path) -> None:
    package_dir = tmp_path / "my_plugin"

    created = create_plugin_template(package_dir)

    assert created == package_dir
    assert (package_dir / "manifest.json").is_file()
    assert (package_dir / "module.py").is_file()
    assert (package_dir / "README.md").is_file()
    assert (package_dir / "requirements.txt").is_file()
    assert (package_dir / "tests" / "test_module.py").is_file()


def test_create_plugin_template_manifest_contains_sdk_version(tmp_path: Path) -> None:
    package_dir = tmp_path / "study_plugin"
    create_plugin_template(package_dir)

    manifest = json.loads((package_dir / "manifest.json").read_text(encoding="utf-8"))

    assert manifest["sdk_version"] == PLUGIN_SDK_VERSION
    assert manifest["capabilities"] == ["study_plugin.analysis"]


def test_generated_template_passes_validation(tmp_path: Path) -> None:
    package_dir = tmp_path / "relationship_plugin"
    create_plugin_template(package_dir)

    manifest = validate_plugin_package(package_dir)

    assert manifest.name == "relationship_plugin"


def test_create_plugin_template_rejects_nonempty_directory(tmp_path: Path) -> None:
    package_dir = tmp_path / "wealth_plugin"
    package_dir.mkdir()
    (package_dir / "existing.txt").write_text("occupied", encoding="utf-8")

    with pytest.raises(ValueError, match="not empty"):
        create_plugin_template(package_dir)
