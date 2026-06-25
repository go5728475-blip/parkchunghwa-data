"""Tests for certification policy enforcer."""

from __future__ import annotations

from core.certification.models import CertificationPolicy, DecisionStatus, PolicyRule
from core.certification.policy_enforcer import CertificationPolicyEnforcer


def _policy(*rules: PolicyRule) -> CertificationPolicy:
    return CertificationPolicy(
        version="1.0",
        id="plugin-cert",
        name="Plugin Certification",
        rules=rules,
    )


def test_enforcer_pass() -> None:
    policy = _policy(
        PolicyRule(
            id="require-manifest",
            severity="fail",
            actions=("block_load",),
            field="manifest",
            required=True,
        ),
    )
    target = {"manifest": {"name": "health"}}

    decision = CertificationPolicyEnforcer().enforce(policy, target, {})

    assert decision.status is DecisionStatus.PASS
    assert not decision.violations


def test_enforcer_warn() -> None:
    policy = _policy(
        PolicyRule(
            id="warn-provider",
            severity="warn",
            actions=("warn",),
            field="source",
            forbidden="openai",
        ),
    )
    target = {"source": "uses openai client"}

    decision = CertificationPolicyEnforcer().enforce(policy, target, {})

    assert decision.status is DecisionStatus.WARN
    assert "warn-provider" in decision.matched_rules
    assert decision.recommendations


def test_enforcer_fail() -> None:
    policy = _policy(
        PolicyRule(
            id="require-manifest",
            severity="fail",
            actions=("block_load",),
            field="manifest",
            required=True,
        ),
    )
    target = {"manifest": None}

    decision = CertificationPolicyEnforcer().enforce(policy, target, {})

    assert decision.status is DecisionStatus.FAIL
    assert decision.violations
    assert "require-manifest" in decision.matched_rules
