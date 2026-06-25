"""Tests for certification policy CLI."""

from __future__ import annotations

import json
from pathlib import Path

from cli.certification import decision_to_exit_code, main, run_check, run_validate
from core.certification.models import (
    CertificationDecision,
    CertificationPolicy,
    DecisionStatus,
    PolicyRule,
)
from core.certification.policy_enforcer import CertificationPolicyEnforcer


VALID_POLICY = {
    "version": "1.0",
    "id": "plugin-cert",
    "name": "Plugin Certification",
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


def _write_policy(tmp_path: Path, name: str, payload: dict | None = None) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload or VALID_POLICY), encoding="utf-8")
    return path


def test_cli_validate_yaml(tmp_path: Path, capsys) -> None:
    policy_path = tmp_path / "policy.yaml"
    policy_path.write_text(
        """
version: "1.0"
id: yaml-policy
name: YAML Policy
rules:
  - id: require-manifest
    severity: fail
    actions:
      - block_load
    field: manifest
    required: true
""".strip(),
        encoding="utf-8",
    )

    exit_code = run_validate(str(policy_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Policy Validated" in captured.out
    assert "yaml-policy" in captured.out


def test_cli_validate_json(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path, "policy.json")

    exit_code = run_validate(str(policy_path))
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "plugin-cert" in captured.out


def test_cli_check_strict_mode(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path, "policy.json")
    target = {"manifest": {"name": "health"}, "source": "openai integration"}

    exit_code = run_check(
        str(policy_path),
        strict=True,
        target=target,
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "WARN" in captured.out


def test_cli_exit_codes() -> None:
    assert decision_to_exit_code(
        CertificationDecision(status=DecisionStatus.PASS),
    ) == 0
    assert decision_to_exit_code(
        CertificationDecision(status=DecisionStatus.WARN),
    ) == 1
    assert decision_to_exit_code(
        CertificationDecision(status=DecisionStatus.FAIL),
    ) == 2


def test_cli_validate_json_output(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path, "policy.json")

    exit_code = run_validate(str(policy_path), output_format="json")
    captured = capsys.readouterr()

    assert exit_code == 0
    json_start = captured.out.index("{")
    payload = json.loads(captured.out[json_start:])
    assert payload["status"] == "PASS"


def test_cli_check_fail_exit_code(tmp_path: Path) -> None:
    policy_path = _write_policy(tmp_path, "policy.json")

    exit_code = run_check(str(policy_path), target={"manifest": None})

    assert exit_code == 2


def test_master_certification_validate_command(tmp_path: Path, capsys) -> None:
    policy_path = _write_policy(tmp_path, "policy.json")

    exit_code = main(["validate", str(policy_path)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Policy Validated" in captured.out


def test_cli_formatted_output() -> None:
    policy = CertificationPolicy(
        version="1.0",
        id="plugin-cert",
        name="Plugin Certification",
        rules=(
            PolicyRule(
                id="require-manifest",
                severity="fail",
                actions=("block_load",),
                field="manifest",
                required=True,
            ),
        ),
    )
    decision = CertificationPolicyEnforcer().enforce(
        policy,
        {"manifest": {"name": "health"}},
        {},
    )

    assert decision.status is DecisionStatus.PASS
