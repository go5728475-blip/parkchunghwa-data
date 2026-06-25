"""End-to-end certification runtime tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.certification import run_check
from core.certification.models import DecisionStatus
from core.runtime.audit_trail import AuditEventType
from core.runtime.bootstrap import RuntimeBootstrap


POLICY_WITH_WARN = {
    "version": "1.0",
    "id": "e2e-policy",
    "name": "E2E Policy",
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


@pytest.fixture
def policy_path(tmp_path: Path) -> Path:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(POLICY_WITH_WARN), encoding="utf-8")
    return path


def test_e2e_pass(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    target = {"manifest": {"name": "health", "version": "1.0.0"}, "source": "sdk module"}

    result = bootstrap.enforce_plugin("health", target)

    assert result.registered is True
    assert result.decision.status is DecisionStatus.PASS
    assert bootstrap.registry.is_registered("health")


def test_e2e_warn(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    target = {
        "manifest": {"name": "health", "version": "1.0.0"},
        "source": "openai integration",
    }

    result = bootstrap.enforce_plugin("health", target)

    assert result.registered is True
    assert result.decision.status is DecisionStatus.WARN
    assert result.warnings


def test_e2e_fail(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)

    result = bootstrap.enforce_plugin("broken", {"manifest": None})

    assert result.registered is False
    assert result.decision.status is DecisionStatus.FAIL
    assert not bootstrap.registry.is_registered("broken")


def test_e2e_manifest_policy_auto_load(tmp_path: Path, policy_path: Path) -> None:
    plugin_dir = tmp_path / "health_plugin"
    plugin_dir.mkdir()
    (plugin_dir / "policy.json").write_text(policy_path.read_text(encoding="utf-8"), encoding="utf-8")
    (plugin_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": "health",
                "version": "1.0.0",
                "author": "test",
                "description": "test",
                "capabilities": ["health.analysis"],
                "module_class": "Module",
                "certification": {"policy": "policy.json"},
            },
        ),
        encoding="utf-8",
    )
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(plugin_path=plugin_dir)

    assert bootstrap.runtime.policy.id == "e2e-policy"


def test_e2e_audit_trail(policy_path: Path) -> None:
    bootstrap = RuntimeBootstrap()
    bootstrap.boot(policy_path=policy_path)
    bootstrap.enforce_plugin(
        "health",
        {"manifest": {"name": "health"}, "source": "openai"},
    )

    events = [entry.event for entry in bootstrap.registry.get_audit_history()]

    assert AuditEventType.POLICY_LOADED in events
    assert AuditEventType.POLICY_VALIDATED in events
    assert AuditEventType.POLICY_ENFORCED in events or AuditEventType.POLICY_FAILED in events


def test_e2e_cli_runtime_check(policy_path: Path, capsys) -> None:
    exit_code = run_check(
        str(policy_path),
        use_runtime=True,
        plugin_id="health",
        target={"manifest": {"name": "health"}, "source": "sdk"},
        show_history=True,
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Runtime Policy Check" in captured.out
    assert "Runtime Audit History" in captured.out
