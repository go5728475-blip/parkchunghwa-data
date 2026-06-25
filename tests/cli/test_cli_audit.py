"""Tests for registry audit CLI commands."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.cli.main import clear_audit_log, list_audit_log
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.audit import RegistryAuditLogger
from core.plugins.registry.audit_json_store import JsonRegistryAuditStore
from core.plugins.registry.certified import CertifiedPluginRecord, CertifiedPluginRegistry
from core.plugins.registry.provider import reset_default_registry
from core.plugins.registry.audit import reset_default_audit_logger


@pytest.fixture(autouse=True)
def _isolated_defaults(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.delenv("MASTER_ENGINE_AUDIT_LOG", raising=False)
    monkeypatch.delenv("MASTER_ENGINE_CERTIFIED_REGISTRY", raising=False)
    monkeypatch.chdir(tmp_path)
    reset_default_registry()
    reset_default_audit_logger()


def test_list_audit_log(capsys, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    logger = RegistryAuditLogger(store=JsonRegistryAuditStore(audit_path))
    registry = CertifiedPluginRegistry(audit_logger=logger)
    registry.register(
        CertifiedPluginRecord(
            plugin_id="health",
            version="1.0.0",
            compatibility_level=PluginCompatibilityLevel.COMPATIBLE,
            certified=True,
        ),
    )

    exit_code = list_audit_log(audit_path=str(audit_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Registry Audit Log" in captured.out
    assert "Plugin ID: health" in captured.out
    assert "Action:    register" in captured.out


def test_clear_audit_log(capsys, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    logger = RegistryAuditLogger(store=JsonRegistryAuditStore(audit_path))
    logger.record_register("wealth", "1.0.0")

    exit_code = clear_audit_log(audit_path=str(audit_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[MASTER ENGINE] Registry Audit Log Cleared" in captured.out

    list_exit = list_audit_log(audit_path=str(audit_path))
    list_captured = capsys.readouterr()
    assert list_exit == 0
    assert "No audit entries." in list_captured.out


def test_empty_audit_log(capsys, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    JsonRegistryAuditStore(audit_path)

    exit_code = list_audit_log(audit_path=str(audit_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "No audit entries." in captured.out


def test_formatted_output(capsys, tmp_path: Path) -> None:
    audit_path = tmp_path / "audit.json"
    logger = RegistryAuditLogger(store=JsonRegistryAuditStore(audit_path))
    logger.record_update("career", "0.2.0", result="success")

    list_audit_log(audit_path=str(audit_path))
    captured = capsys.readouterr()

    assert "Timestamp:" in captured.out
    assert "Action:    update" in captured.out
    assert "Plugin ID: career" in captured.out
    assert "Version:   0.2.0" in captured.out
    assert "Result:    success" in captured.out
