"""Certification policy validation."""

from __future__ import annotations

import logging

from core.certification.errors import PolicyValidationError
from core.certification.models import VALID_SEVERITIES, CertificationPolicy, ValidationResult

logger = logging.getLogger("certification.policy.validate")


class CertificationPolicyValidator:
    """Validates certification policy documents."""

    def validate(self, policy: CertificationPolicy) -> ValidationResult:
        logger.info("Validating certification policy %s", policy.id)
        errors: list[str] = []
        if not policy.version.strip():
            errors.append("version is required")
        if not policy.id.strip():
            errors.append("id is required")
        if not policy.name.strip():
            errors.append("name is required")
        if not policy.rules:
            errors.append("rules must contain at least one rule")
        for rule in policy.rules:
            if not rule.id.strip():
                errors.append("rule id is required")
            if rule.severity not in VALID_SEVERITIES:
                errors.append(
                    f"rule {rule.id} has invalid severity: {rule.severity}",
                )
            if not rule.actions:
                errors.append(f"rule {rule.id} actions must not be empty")
        result = ValidationResult(valid=not errors, errors=tuple(errors))
        if not result.valid:
            raise PolicyValidationError(
                "Policy validation failed",
                errors=result.errors,
            )
        return result
