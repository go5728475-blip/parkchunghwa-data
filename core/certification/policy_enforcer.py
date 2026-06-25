"""Certification policy enforcement."""

from __future__ import annotations

import logging
from typing import Any

from core.certification.models import (
    CertificationDecision,
    CertificationPolicy,
    DecisionStatus,
    PolicyRule,
)

logger = logging.getLogger("certification.policy.enforce")


class CertificationPolicyEnforcer:
    """Enforces certification policies against runtime targets."""

    def enforce(
        self,
        policy: CertificationPolicy,
        target: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> CertificationDecision:
        logger.info("Enforcing certification policy %s", policy.id)
        runtime_context = context or {}
        violations: list[str] = []
        recommendations: list[str] = []
        matched_rules: list[str] = []
        has_fail = False
        has_warn = False

        for rule in policy.rules:
            matched, message = _evaluate_rule(rule, target, runtime_context)
            if not matched:
                continue
            matched_rules.append(rule.id)
            if rule.severity == "fail":
                has_fail = True
                violations.append(message or f"rule {rule.id} failed")
            elif rule.severity == "warn":
                has_warn = True
                recommendations.append(message or f"rule {rule.id} warning")
            else:
                recommendations.append(message or f"rule {rule.id} info")

        if has_fail:
            status = DecisionStatus.FAIL
        elif has_warn:
            status = DecisionStatus.WARN
        else:
            status = DecisionStatus.PASS

        return CertificationDecision(
            status=status,
            violations=tuple(violations),
            recommendations=tuple(recommendations),
            matched_rules=tuple(matched_rules),
        )


def _evaluate_rule(
    rule: PolicyRule,
    target: dict[str, Any],
    context: dict[str, Any],
) -> tuple[bool, str | None]:
    if rule.field is None:
        return False, None
    value = target.get(rule.field)
    if context.get("expected_version") and rule.id == "version-match":
        if str(value) != str(context["expected_version"]):
            return True, (
                f"version mismatch: target={value}, expected={context['expected_version']}"
            )
        return False, None
    if rule.required and not value:
        return True, f"required field missing or empty: {rule.field}"
    if rule.forbidden and value is not None and rule.forbidden in str(value):
        return True, f"forbidden value in {rule.field}: {rule.forbidden}"
    return False, None
