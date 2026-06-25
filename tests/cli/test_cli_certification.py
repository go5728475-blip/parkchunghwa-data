"""Tests for certify-plugin CLI command."""

from __future__ import annotations

import json
from pathlib import Path

from core.cli.main import certify_plugin
from core.plugins.certification.compatibility import map_result_to_compatibility_level
from core.plugins.certification.result import PluginCertificationResult


FIXTURES_DIR = Path(__file__).resolve().parents[1] / "fixtures" / "plugins"
HEALTH_PLUGIN_DIR = FIXTURES_DIR / "health_plugin"


def _write_warning_plugin(package_dir: Path) -> None:
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "provider_bound",
                "version": "1.0.0",
                "author": "Developer",
                "description": "Provider bound plugin",
                "capabilities": ["provider_bound.analysis"],
                "module_class": "Module",
                "sdk_version": "1.0.0",
            },
        ),
        encoding="utf-8",
    )
    (package_dir / "module.py").write_text(
        '''
"""Provider-bound plugin."""

from sdk import BaseModule


class Module(BaseModule):
  """openai integration placeholder."""

  def __init__(self) -> None:
    super().__init__(
      name="provider_bound",
      version="1.0.0",
      capabilities=("provider_bound.analysis",),
    )
''',
        encoding="utf-8",
    )


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


def test_cli_certify_plugin_success_for_valid_fixture(capsys) -> None:
    exit_code = certify_plugin(str(HEALTH_PLUGIN_DIR))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Plugin Certification" in captured.out
    assert "Plugin ID:           health" in captured.out
    assert "Passed:              True" in captured.out


def test_cli_certify_plugin_fails_for_invalid_plugin(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "invalid_plugin"
    _write_invalid_plugin(package_dir)

    exit_code = certify_plugin(str(package_dir))
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "Passed:              False" in captured.out
    assert "Compatibility Level: INCOMPATIBLE" in captured.out
    assert "Errors:" in captured.out


def test_cli_certify_plugin_succeeds_with_warnings_only(capsys, tmp_path: Path) -> None:
    package_dir = tmp_path / "warning_plugin"
    _write_warning_plugin(package_dir)

    exit_code = certify_plugin(str(package_dir))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Passed:              True" in captured.out
    assert "Warnings:" in captured.out
    assert "openai" in captured.out.lower()


def test_cli_certify_plugin_output_includes_compatibility_level(capsys) -> None:
    exit_code = certify_plugin(str(HEALTH_PLUGIN_DIR))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Compatibility Level: COMPATIBLE" in captured.out


def test_cli_certify_plugin_output_includes_checks(capsys) -> None:
    exit_code = certify_plugin(str(HEALTH_PLUGIN_DIR))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "manifest_required" in captured.out
    assert "lifecycle" in captured.out


def test_map_result_to_compatibility_level_rules() -> None:
    passed = PluginCertificationResult.pass_result("wealth")
    warned = PluginCertificationResult(
        plugin_id="wealth",
        passed=True,
        warnings=("provider warning",),
    )
    failed = PluginCertificationResult.fail_result("wealth", errors=("broken",))

    assert map_result_to_compatibility_level(passed) == "COMPATIBLE"
    assert map_result_to_compatibility_level(warned) == "PARTIAL"
    assert map_result_to_compatibility_level(failed) == "INCOMPATIBLE"
    assert map_result_to_compatibility_level(None) == "UNKNOWN"
