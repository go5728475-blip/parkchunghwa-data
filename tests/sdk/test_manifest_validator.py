"""Tests for SDK manifest validation."""

from __future__ import annotations

from pathlib import Path

import pytest

from sdk.validation import ValidationError, validate_manifest, validate_manifest_file
from sdk.version import PLUGIN_SDK_VERSION


def test_validate_manifest_accepts_valid_payload() -> None:
    manifest = validate_manifest(
        {
            "name": "wealth",
            "version": "1.0.0",
            "author": "Developer",
            "description": "Wealth engine",
            "capabilities": ["wealth.analysis"],
            "module_class": "Module",
            "sdk_version": PLUGIN_SDK_VERSION,
        },
    )

    assert manifest.name == "wealth"
    assert manifest.capabilities == ("wealth.analysis",)


def test_validate_manifest_rejects_missing_field() -> None:
    with pytest.raises(ValidationError, match="missing required field"):
        validate_manifest(
            {
                "name": "wealth",
                "version": "1.0.0",
                "author": "Developer",
                "description": "Wealth engine",
                "capabilities": ["wealth.analysis"],
            },
        )


def test_validate_manifest_rejects_invalid_version() -> None:
    with pytest.raises(ValidationError, match="semantic version"):
        validate_manifest(
            {
                "name": "wealth",
                "version": "v1",
                "author": "Developer",
                "description": "Wealth engine",
                "capabilities": ["wealth.analysis"],
                "module_class": "Module",
            },
        )


def test_validate_manifest_rejects_incompatible_sdk_version() -> None:
    with pytest.raises(ValidationError, match="Incompatible sdk_version"):
        validate_manifest(
            {
                "name": "wealth",
                "version": "1.0.0",
                "author": "Developer",
                "description": "Wealth engine",
                "capabilities": ["wealth.analysis"],
                "module_class": "Module",
                "sdk_version": "2.0.0",
            },
        )


def test_validate_manifest_file_reads_package_manifest(tmp_path: Path) -> None:
    package_dir = tmp_path / "career_plugin"
    package_dir.mkdir()
    (package_dir / "manifest.json").write_text(
        """
        {
          "name": "career",
          "version": "0.1.0",
          "author": "Developer",
          "description": "Career engine",
          "capabilities": ["career.analysis"],
          "module_class": "Module",
          "sdk_version": "1.0.0"
        }
        """.strip(),
        encoding="utf-8",
    )

    manifest = validate_manifest_file(package_dir)

    assert manifest.name == "career"
