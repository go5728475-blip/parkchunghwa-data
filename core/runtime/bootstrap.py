"""Runtime bootstrap with certification policy integration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from core.plugins.plugin_registry import CertificationPluginRegistry
from core.runtime.certification_runtime import CertificationRuntime, RuntimeDecision
from core.runtime.paths import ensure_default_certification_policy_file

logger = logging.getLogger("certification.policy.load")


class RuntimeBootstrap:
    """Bootstraps runtime services including certification policy enforcement."""

    def __init__(
        self,
        runtime: CertificationRuntime | None = None,
        registry: CertificationPluginRegistry | None = None,
    ) -> None:
        self._registry = registry or CertificationPluginRegistry()
        self._runtime = runtime or CertificationRuntime(registry=self._registry)
        self._booted = False

    @property
    def runtime(self) -> CertificationRuntime:
        return self._runtime

    @property
    def registry(self) -> CertificationPluginRegistry:
        return self._registry

    @property
    def is_booted(self) -> bool:
        return self._booted

    def boot(
        self,
        *,
        policy_path: str | Path | None = None,
        plugin_path: str | Path | None = None,
    ) -> CertificationRuntime:
        resolved_policy = self._resolve_policy_path(policy_path, plugin_path)
        self._runtime.initialize(resolved_policy)
        self._booted = True
        logger.info("Runtime bootstrap completed with policy %s", self._runtime.policy.id)
        return self._runtime

    def enforce_plugin(
        self,
        plugin_id: str,
        target: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> RuntimeDecision:
        if not self._booted:
            self.boot()
        return self._runtime.enforce_plugin_load(plugin_id, target, context)

    def reload_policy(self, path: str | Path | None = None) -> object:
        if not self._booted:
            self.boot(policy_path=path)
            return self._runtime.policy
        return self._runtime.reload_policy(path)

    def registry_bridge(self, certified_registry: object | None = None) -> object:
        from core.runtime.registry_bridge import RuntimeRegistryBridge

        return RuntimeRegistryBridge(self._registry, certified_registry)

    @staticmethod
    def parse_policy_option(args: list[str]) -> tuple[str | None, list[str]]:
        policy_path: str | None = None
        remaining: list[str] = []
        index = 0
        while index < len(args):
            token = args[index]
            if token == "--policy" and index + 1 < len(args):
                policy_path = args[index + 1]
                index += 2
                continue
            remaining.append(token)
            index += 1
        return policy_path, remaining

    def _resolve_policy_path(
        self,
        policy_path: str | Path | None,
        plugin_path: str | Path | None,
    ) -> Path:
        if policy_path is not None:
            return Path(policy_path)
        if plugin_path is not None:
            manifest_policy = CertificationRuntime.resolve_manifest_policy_path(plugin_path)
            if manifest_policy is not None and manifest_policy.exists():
                return manifest_policy
        return ensure_default_certification_policy_file()
