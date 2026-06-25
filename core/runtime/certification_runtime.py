"""Certification policy runtime orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from core.certification.errors import PolicyLoadError, PolicyValidationError
from core.certification.models import CertificationDecision, CertificationPolicy, DecisionStatus
from core.certification.policy_enforcer import CertificationPolicyEnforcer
from core.certification.policy_loader import CertificationPolicyLoader
from core.certification.policy_validator import CertificationPolicyValidator
from core.plugins.plugin_registry import CertificationPluginRegistry
from core.runtime.audit_trail import AuditEventType
from core.runtime.paths import ensure_default_certification_policy_file
from core.runtime.policy_cache import RuntimePolicyCache, get_default_policy_cache

logger = logging.getLogger("certification.policy.enforce")

CACHE_HIT = "POLICY_CACHE_HIT"
CACHE_MISS = "POLICY_CACHE_MISS"


@dataclass(frozen=True, kw_only=True)
class RuntimeDecision:
    """Runtime outcome including registration eligibility."""

    decision: CertificationDecision
    registered: bool
    plugin_id: str | None = None
    warnings: tuple[str, ...] = ()


class CertificationRuntime:
    """Loads, validates, and enforces certification policies at runtime."""

    def __init__(
        self,
        registry: CertificationPluginRegistry | None = None,
        loader: CertificationPolicyLoader | None = None,
        validator: CertificationPolicyValidator | None = None,
        enforcer: CertificationPolicyEnforcer | None = None,
        policy_cache: RuntimePolicyCache | None = None,
    ) -> None:
        self._registry = registry or CertificationPluginRegistry()
        self._loader = loader or CertificationPolicyLoader()
        self._validator = validator or CertificationPolicyValidator()
        self._enforcer = enforcer or CertificationPolicyEnforcer()
        self._policy_cache = policy_cache or get_default_policy_cache()
        self._policy: CertificationPolicy | None = None
        self._policy_path: Path | None = None
        self._last_decision: CertificationDecision | None = None
        self._initialized = False

    @property
    def policy_cache(self) -> RuntimePolicyCache:
        return self._policy_cache

    @property
    def policy_path(self) -> Path | None:
        return self._policy_path

    @property
    def registry(self) -> CertificationPluginRegistry:
        return self._registry

    @property
    def policy(self) -> CertificationPolicy | None:
        return self._policy

    @property
    def last_decision(self) -> CertificationDecision | None:
        return self._last_decision

    def initialize(self, policy_path: str | Path | None = None) -> CertificationPolicy:
        resolved = Path(policy_path) if policy_path else ensure_default_certification_policy_file()
        self.load_policy(resolved)
        self.validate()
        self._initialized = True
        return self._policy  # type: ignore[return-value]

    def load_policy(self, path: str | Path) -> CertificationPolicy:
        resolved = Path(path).resolve()
        cached = self._policy_cache.get(resolved)
        if cached is not None:
            self._policy = cached
            self._policy_path = resolved
            self._registry.set_policy(cached)
            self._registry.audit_trail.record(
                CACHE_HIT,
                policy_id=cached.id,
            )
            logger.info("Policy cache hit for %s", resolved)
            return cached
        policy = self._loader.load(resolved)
        self._policy_cache.put(resolved, policy)
        self._policy = policy
        self._policy_path = resolved
        self._registry.set_policy(policy)
        self._registry.audit_trail.record(
            CACHE_MISS,
            policy_id=policy.id,
        )
        self._registry.audit_trail.record(
            AuditEventType.POLICY_LOADED,
            policy_id=policy.id,
        )
        logger.info("Loaded certification policy %s", policy.id)
        return policy

    def reload_policy(self, path: str | Path | None = None) -> CertificationPolicy:
        resolved = Path(path or self._policy_path or ensure_default_certification_policy_file())
        policy = self._policy_cache.reload(resolved, self._loader)
        self._policy = policy
        self._policy_path = resolved.resolve()
        self._registry.set_policy(policy)
        self._registry.audit_trail.record(
            AuditEventType.POLICY_LOADED,
            policy_id=policy.id,
        )
        self.validate()
        self._reevaluate_registered_plugins()
        return policy

    def invalidate_policy_cache(self, path: str | Path | None = None) -> None:
        if path is not None:
            self._policy_cache.invalidate(path)
            return
        if self._policy_path is not None:
            self._policy_cache.invalidate(self._policy_path)

    def clear_policy_cache(self) -> None:
        self._policy_cache.clear()

    def validate(self) -> None:
        if self._policy is None:
            msg = "Policy must be loaded before validation"
            raise PolicyValidationError(msg)
        self._validator.validate(self._policy)
        self._registry.audit_trail.record(
            AuditEventType.POLICY_VALIDATED,
            policy_id=self._policy.id,
        )

    def enforce(
        self,
        target: dict[str, Any],
        context: dict[str, Any] | None = None,
        *,
        plugin_id: str | None = None,
    ) -> CertificationDecision:
        if self._policy is None:
            msg = "Policy must be loaded before enforcement"
            raise PolicyLoadError(msg)
        decision = self._enforcer.enforce(self._policy, target, context)
        self._last_decision = decision
        event = (
            AuditEventType.POLICY_FAILED
            if decision.status is DecisionStatus.FAIL
            else AuditEventType.POLICY_ENFORCED
        )
        self._registry.audit_trail.record(
            event,
            policy_id=self._policy.id,
            plugin_id=plugin_id,
            decision=decision.status.value,
            violations=decision.violations,
        )
        if plugin_id is not None:
            self._registry.set_decision(
                plugin_id,
                decision,
                warnings=decision.recommendations,
            )
        return decision

    def enforce_plugin_load(
        self,
        plugin_id: str,
        target: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> RuntimeDecision:
        decision = self.enforce(target, context, plugin_id=plugin_id)
        if decision.status is DecisionStatus.FAIL:
            return RuntimeDecision(
                decision=decision,
                registered=False,
                plugin_id=plugin_id,
            )
        if decision.status is DecisionStatus.WARN:
            return RuntimeDecision(
                decision=decision,
                registered=True,
                plugin_id=plugin_id,
                warnings=decision.recommendations,
            )
        return RuntimeDecision(
            decision=decision,
            registered=True,
            plugin_id=plugin_id,
        )

    @staticmethod
    def resolve_manifest_policy_path(
        plugin_path: str | Path,
    ) -> Path | None:
        manifest_path = _resolve_manifest_path(plugin_path)
        if not manifest_path.exists():
            return None
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return None
        certification = payload.get("certification")
        if not isinstance(certification, dict):
            return None
        policy_ref = certification.get("policy")
        if not policy_ref:
            return None
        base_dir = manifest_path.parent
        return (base_dir / str(policy_ref)).resolve()

    def _reevaluate_registered_plugins(self) -> None:
        if self._policy is None:
            return
        for plugin_id in self._registry.list_runtime_plugins():
            prior = self._registry.get_decision(plugin_id)
            if prior is None:
                continue
            target = {"manifest": {"name": plugin_id}, "source": ""}
            decision = self.enforce(target, plugin_id=plugin_id)
            self._registry.update_decision_metadata(
                plugin_id,
                decision,
                warnings=decision.recommendations,
            )


def _resolve_manifest_path(plugin_path: str | Path) -> Path:
    candidate = Path(plugin_path)
    if candidate.is_dir():
        return candidate / "manifest.json"
    return candidate
