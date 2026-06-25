"""Certification policy domain models."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DecisionStatus(StrEnum):
    """Enforcement decision status."""

    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


VALID_SEVERITIES = frozenset({"fail", "warn", "info"})


@dataclass(frozen=True, kw_only=True)
class PolicyRule:
    """Single enforceable certification rule."""

    id: str
    severity: str
    actions: tuple[str, ...]
    field: str | None = None
    required: bool = False
    forbidden: str | None = None


@dataclass(frozen=True, kw_only=True)
class CertificationPolicy:
    """Declarative certification policy document."""

    version: str
    id: str
    name: str
    rules: tuple[PolicyRule, ...]


@dataclass(frozen=True, kw_only=True)
class ValidationResult:
    """Outcome of policy schema validation."""

    valid: bool
    errors: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class CertificationDecision:
    """Outcome of policy enforcement against a target."""

    status: DecisionStatus
    violations: tuple[str, ...] = ()
    recommendations: tuple[str, ...] = ()
    matched_rules: tuple[str, ...] = ()
