"""Certification plugin registry for runtime policy state."""

from __future__ import annotations

from core.certification.models import CertificationDecision, CertificationPolicy
from core.runtime.audit_trail import CertificationAuditTrail, PolicyAuditEntry


class CertificationPluginRegistry:
    """Tracks loaded policies, enforcement decisions, and audit history."""

    def __init__(self, audit_trail: CertificationAuditTrail | None = None) -> None:
        self._policy: CertificationPolicy | None = None
        self._decisions: dict[str, CertificationDecision] = {}
        self._warnings: dict[str, tuple[str, ...]] = {}
        self._audit_trail = audit_trail or CertificationAuditTrail()

    @property
    def audit_trail(self) -> CertificationAuditTrail:
        return self._audit_trail

    def set_policy(self, policy: CertificationPolicy) -> None:
        self._policy = policy

    def get_policy(self) -> CertificationPolicy | None:
        return self._policy

    def set_decision(
        self,
        plugin_id: str,
        decision: CertificationDecision,
        *,
        warnings: tuple[str, ...] = (),
    ) -> None:
        self._decisions[plugin_id] = decision
        if warnings:
            self._warnings[plugin_id] = warnings

    def get_decision(self, plugin_id: str) -> CertificationDecision | None:
        return self._decisions.get(plugin_id)

    def get_warnings(self, plugin_id: str) -> tuple[str, ...]:
        return self._warnings.get(plugin_id, ())

    def is_registered(self, plugin_id: str) -> bool:
        decision = self._decisions.get(plugin_id)
        if decision is None:
            return False
        return decision.status.value != "FAIL"

    def get_audit_history(self) -> tuple[PolicyAuditEntry, ...]:
        return self._audit_trail.history()

    def list_runtime_plugins(self) -> tuple[str, ...]:
        return tuple(sorted(self._decisions))

    def update_decision_metadata(
        self,
        plugin_id: str,
        decision: CertificationDecision,
        *,
        warnings: tuple[str, ...] = (),
    ) -> None:
        """Refresh runtime decision metadata without unloading the plugin."""
        self.set_decision(plugin_id, decision, warnings=warnings)
