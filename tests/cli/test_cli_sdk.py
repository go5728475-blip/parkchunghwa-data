"""Tests for SDK CLI commands."""

from __future__ import annotations

from pathlib import Path

from core.cli.main import create_plugin, validate_plugin
from sdk.validation import validate_plugin_package


def test_cli_create_plugin_generates_template(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "academic_plugin"

    exit_code = create_plugin(str(package_dir))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Plugin Template Created" in captured.out
    assert package_dir.is_dir()
    assert (package_dir / "manifest.json").is_file()


def test_cli_validate_plugin_accepts_generated_template(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "wellness_plugin"
    create_plugin(str(package_dir))

    exit_code = validate_plugin(str(package_dir))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Plugin Validated" in captured.out
    assert "wellness_plugin" in captured.out


def test_cli_validate_plugin_reports_failure(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "broken_plugin"
    package_dir.mkdir()

    exit_code = validate_plugin(str(package_dir))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] ValidatePlugin failed" in captured.out


def test_generated_plugin_can_be_validated_by_sdk(tmp_path: Path) -> None:
    package_dir = tmp_path / "career_plugin"
    create_plugin(str(package_dir))

    manifest = validate_plugin_package(package_dir)

    assert manifest.name == "career_plugin"
    assert manifest.capabilities == ("career_plugin.analysis",)
