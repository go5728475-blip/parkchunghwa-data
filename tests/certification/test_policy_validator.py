"""Tests for certification policy validator."""

from __future__ import annotations

import pytest

from core.certification.errors import PolicyValidationError
from core.certification.models import CertificationPolicy, PolicyRule
from core.certification.policy_validator import CertificationPolicyValidator


def _policy(**overrides: object) -> CertificationPolicy:
    base = {
        "version": "1.0",
        "id": "plugin-cert",
        "name": "Plugin Certification",
        "rules": (
            PolicyRule(
                id="require-manifest",
                severity="fail",
                actions=("block_load",),
                field="manifest",
                required=True,
            ),
        ),
    }
    base.update(overrides)
    return CertificationPolicy(**base)


def test_valid_policy_passes() -> None:
    result = CertificationPolicyValidator().validate(_policy())

    assert result.valid is True
    assert not result.errors


def test_missing_version_fails() -> None:
    with pytest.raises(PolicyValidationError) as exc_info:
        CertificationPolicyValidator().validate(_policy(version=""))

    assert any("version" in error for error in exc_info.value.errors)


def test_missing_rules_fails() -> None:
    with pytest.raises(PolicyValidationError) as exc_info:
        CertificationPolicyValidator().validate(_policy(rules=()))

    assert any("rules" in error for error in exc_info.value.errors)


def test_invalid_severity_fails() -> None:
    policy = _policy(
        rules=(
            PolicyRule(
                id="bad-severity",
                severity="critical",
                actions=("block",),
            ),
        ),
    )

    with pytest.raises(PolicyValidationError) as exc_info:
        CertificationPolicyValidator().validate(policy)

    assert any("invalid severity" in error for error in exc_info.value.errors)
