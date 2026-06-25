"""Tests for certification runtime."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.certification.models import DecisionStatus
from core.runtime.certification_runtime import CertificationRuntime


VALID_POLICY = {
    "version": "1.0",
    "id": "runtime-policy",
    "name": "Runtime Policy",
    "rules": [
        {
            "id": "require-manifest",
            "severity": "fail",
            "actions": ["block_load"],
            "field": "manifest",
            "required": True,
        },
    ],
}


@pytest.fixture
def policy_file(tmp_path: Path) -> Path:
    path = tmp_path / "policy.json"
    path.write_text(json.dumps(VALID_POLICY), encoding="utf-8")
    return path


def test_runtime_initialize(policy_file: Path) -> None:
    runtime = CertificationRuntime()

    policy = runtime.initialize(policy_file)

    assert policy.id == "runtime-policy"
    assert runtime.registry.get_policy() == policy


def test_runtime_load(policy_file: Path) -> None:
    runtime = CertificationRuntime()

    policy = runtime.load_policy(policy_file)

    assert policy.name == "Runtime Policy"
    history = runtime.registry.get_audit_history()
    assert history[-1].event == "POLICY_LOADED"


def test_runtime_validate(policy_file: Path) -> None:
    runtime = CertificationRuntime()
    runtime.load_policy(policy_file)

    runtime.validate()

    events = [entry.event for entry in runtime.registry.get_audit_history()]
    assert "POLICY_VALIDATED" in events


def test_runtime_enforce_pass(policy_file: Path) -> None:
    runtime = CertificationRuntime()
    runtime.initialize(policy_file)

    decision = runtime.enforce(
        {"manifest": {"name": "health", "version": "1.0.0"}},
        plugin_id="health",
    )

    assert decision.status is DecisionStatus.PASS
    assert runtime.registry.get_decision("health") is not None


def test_runtime_enforce_fail(policy_file: Path) -> None:
    runtime = CertificationRuntime()
    runtime.initialize(policy_file)

    decision = runtime.enforce({"manifest": None}, plugin_id="broken")

    assert decision.status is DecisionStatus.FAIL
    assert runtime.registry.get_audit_history()[-1].event == "POLICY_FAILED"
