"""Tests for certified plugin load gate CLI integration."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.bootstrap.bootstrap import Bootstrap
from core.cli.main import load_module, main, register_certified


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


def _write_invalid_plugin(package_dir: Path) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "invalid",
                "version": "1.0.0",
                "author": "Developer",
                "description": "Invalid plugin",
                "capabilities": ["invalid.analysis"],
                "module_class": "Module",
                "sdk_version": "2.0.0",
            },
        ),
        encoding="utf-8",
    )
    (package_dir / "module.py").write_text(
        '''
from sdk import BaseModule


class Module(BaseModule):
  def __init__(self) -> None:
    super().__init__(
      name="invalid",
      version="1.0.0",
      capabilities=("invalid.analysis",),
    )
''',
        encoding="utf-8",
    )


def test_load_module_without_certified_only_keeps_existing_behavior(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Loaded" in captured.out
    assert "Module Name: health" in captured.out
    assert "Certified:" not in captured.out
    assert bootstrap.module_registry().exists("health")


def test_load_module_certified_only_valid_plugin_succeeds(capsys) -> None:
    bootstrap = Bootstrap().build()
    exit_code = load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Module Loaded" in captured.out
    assert "Certified:           True" in captured.out
    assert "Compatibility Level: COMPATIBLE" in captured.out
    assert bootstrap.module_registry().exists("health")


def test_load_module_certified_only_invalid_plugin_fails(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "invalid_plugin"
    _write_invalid_plugin(package_dir)
    bootstrap = Bootstrap().build()

    exit_code = load_module(
        str(package_dir),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] LoadModule failed" in captured.out
    assert "Plugin certification failed for invalid" in captured.out
    assert not bootstrap.module_registry().exists("invalid")


def test_register_certified_valid_plugin_succeeds(capsys) -> None:
    exit_code = register_certified(str(HEALTH_PLUGIN_DIR))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Certified Plugin Registered" in captured.out
    assert "Plugin ID:           health" in captured.out
    assert "Certified:           True" in captured.out


def test_register_certified_invalid_plugin_fails(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "invalid_plugin"
    _write_invalid_plugin(package_dir)

    exit_code = register_certified(str(package_dir))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "[MASTER ENGINE] RegisterCertified failed" in captured.out
    assert "Plugin ID: invalid" in captured.out


def test_output_includes_compatibility_level(capsys) -> None:
    bootstrap = Bootstrap().build()
    load_module(
        str(HEALTH_PLUGIN_DIR),
        loader_manager=bootstrap.loader_manager(),
        certified_only=True,
    )
    captured = capsys.readouterr()

    assert "Compatibility Level: COMPATIBLE" in captured.out

    capsys.readouterr()
    register_certified(str(HEALTH_PLUGIN_DIR))
    captured = capsys.readouterr()

    assert "Compatibility Level: COMPATIBLE" in captured.out


def test_main_load_module_parses_certified_only_flag(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["load-module", "--certified-only", str(HEALTH_PLUGIN_DIR)])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Compatibility Level: COMPATIBLE" in captured.out
