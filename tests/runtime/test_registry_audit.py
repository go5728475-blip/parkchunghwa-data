"""Tests for certification plugin registry audit trail."""

from __future__ import annotations

from core.certification.models import CertificationDecision, DecisionStatus
from core.plugins.plugin_registry import CertificationPluginRegistry
from core.runtime.audit_trail import AuditEventType, CertificationAuditTrail


def test_audit_append_and_history() -> None:
    trail = CertificationAuditTrail()
    trail.record(AuditEventType.POLICY_LOADED, policy_id="runtime-policy")
    trail.record(
        AuditEventType.POLICY_ENFORCED,
        policy_id="runtime-policy",
        plugin_id="health",
        decision="PASS",
    )

    history = trail.history()

    assert len(history) == 2
    assert history[0].event == "POLICY_LOADED"
    assert history[1].plugin_id == "health"


def test_registry_get_policy_and_decision() -> None:
    from core.certification.models import CertificationPolicy, PolicyRule

    registry = CertificationPluginRegistry()
    policy = CertificationPolicy(
        version="1.0",
        id="runtime-policy",
        name="Runtime Policy",
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
    decision = CertificationDecision(status=DecisionStatus.PASS)

    registry.set_policy(policy)
    registry.set_decision("health", decision)

    assert registry.get_policy() == policy
    assert registry.get_decision("health") == decision


def test_registry_audit_history_delegates_to_trail() -> None:
    registry = CertificationPluginRegistry()
    registry.audit_trail.record(
        AuditEventType.POLICY_FAILED,
        policy_id="runtime-policy",
        plugin_id="broken",
        decision="FAIL",
        violations=("required field missing",),
    )

    history = registry.get_audit_history()

    assert len(history) == 1
    assert history[0].event == "POLICY_FAILED"
    assert history[0].violations
