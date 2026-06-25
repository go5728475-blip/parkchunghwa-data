"""Tests for certification policy loader."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.certification.errors import PolicyLoadError
from core.certification.policy_loader import (
    CertificationPolicyLoader,
    PolicyLoaderRegistry,
)


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
    ],
}


def test_load_json_policy(tmp_path: Path) -> None:
    policy_path = tmp_path / "policy.json"
    policy_path.write_text(json.dumps(VALID_POLICY), encoding="utf-8")

    policy = CertificationPolicyLoader().load(policy_path)

    assert policy.id == "plugin-cert"
    assert policy.version == "1.0"
    assert len(policy.rules) == 1


def test_load_yaml_policy(tmp_path: Path) -> None:
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

    policy = CertificationPolicyLoader().load(policy_path)

    assert policy.id == "yaml-policy"
    assert policy.rules[0].field == "manifest"


def test_invalid_file_raises(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"

    with pytest.raises(PolicyLoadError, match="not found"):
        CertificationPolicyLoader().load(missing)


def test_invalid_schema_raises(tmp_path: Path) -> None:
    policy_path = tmp_path / "invalid.json"
    policy_path.write_text(json.dumps({"name": "missing fields"}), encoding="utf-8")

    with pytest.raises(PolicyLoadError):
        CertificationPolicyLoader().load(policy_path)


def test_policy_loader_registry_register_and_resolve(tmp_path: Path) -> None:
    registry = PolicyLoaderRegistry()
    registry.register(".txt", lambda text: json.loads(text))
    loader = CertificationPolicyLoader(registry=registry)
    policy_path = tmp_path / "policy.txt"
    policy_path.write_text(json.dumps(VALID_POLICY), encoding="utf-8")

    policy = loader.load(policy_path)

    assert policy.name == "Plugin Certification"
