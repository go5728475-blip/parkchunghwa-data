"""Built-in plugin certification checks."""

from __future__ import annotations

import inspect

from sdk.version import PLUGIN_SDK_VERSION

from core.plugins.certification.result import PluginCertificationResult

_FORBIDDEN_PROVIDER_TOKENS = ("openai", "anthropic", "gemini", "claude")


def _plugin_id(plugin: object) -> str:
    manifest = getattr(plugin, "manifest", None)
    if manifest is not None:
        name = getattr(manifest, "name", None)
        if name:
            return str(name)
    name_attr = getattr(plugin, "name", None)
    if callable(name_attr):
        return str(name_attr())
    if isinstance(name_attr, str) and name_attr:
        return name_attr
    return plugin.__class__.__name__


def _capabilities_value(plugin: object) -> object | None:
    manifest = getattr(plugin, "manifest", None)
    if manifest is not None:
        return getattr(manifest, "capabilities", None)
    capabilities = getattr(plugin, "capabilities", None)
    if callable(capabilities):
        return capabilities()
    return capabilities


class ManifestRequiredCheck:
    """Ensure plugin manifest contains required metadata."""

    name = "manifest_required"

    def check(self, plugin: object) -> PluginCertificationResult:
        plugin_id = _plugin_id(plugin)
        manifest = getattr(plugin, "manifest", None)
        if manifest is None:
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=("Plugin manifest is required.",),
                checks=(self.name,),
            )

        errors: list[str] = []
        if not getattr(manifest, "name", None):
            errors.append("Manifest name is required.")
        if not getattr(manifest, "version", None):
            errors.append("Manifest version is required.")
        if getattr(manifest, "capabilities", None) is None:
            errors.append("Manifest capabilities are required.")

        if errors:
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=tuple(errors),
                checks=(self.name,),
            )
        return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))


class LifecycleCheck:
    """Ensure plugin exposes boot and shutdown lifecycle hooks."""

    name = "lifecycle"

    def check(self, plugin: object) -> PluginCertificationResult:
        plugin_id = _plugin_id(plugin)
        errors: list[str] = []
        boot = getattr(plugin, "boot", None)
        shutdown = getattr(plugin, "shutdown", None)
        if not callable(boot):
            errors.append("Plugin boot() is required.")
        if not callable(shutdown):
            errors.append("Plugin shutdown() is required.")

        if errors:
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=tuple(errors),
                checks=(self.name,),
            )
        return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))


class CapabilityDeclarationCheck:
    """Ensure plugin declares non-empty capabilities."""

    name = "capability_declaration"

    def check(self, plugin: object) -> PluginCertificationResult:
        plugin_id = _plugin_id(plugin)
        capabilities = _capabilities_value(plugin)
        if capabilities is None:
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=("Plugin capabilities are required.",),
                checks=(self.name,),
            )
        if not isinstance(capabilities, tuple | list | set):
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=("Plugin capabilities must be a tuple, list, or set.",),
                checks=(self.name,),
            )
        if not capabilities:
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=("Plugin capabilities cannot be empty.",),
                checks=(self.name,),
            )
        return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))


class SDKVersionCheck:
    """Ensure manifest sdk_version matches PLUGIN_SDK_VERSION major.minor."""

    name = "sdk_version"

    def check(self, plugin: object) -> PluginCertificationResult:
        plugin_id = _plugin_id(plugin)
        manifest = getattr(plugin, "manifest", None)
        if manifest is None:
            return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))

        sdk_version = getattr(manifest, "sdk_version", None)
        if sdk_version is None:
            return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))

        manifest_major, manifest_minor, _ = str(sdk_version).split(".")
        sdk_major, sdk_minor, _ = PLUGIN_SDK_VERSION.split(".")
        if (manifest_major, manifest_minor) != (sdk_major, sdk_minor):
            return PluginCertificationResult.fail_result(
                plugin_id,
                errors=(
                    f"Incompatible sdk_version {sdk_version}; "
                    f"expected {sdk_major}.{sdk_minor}.x",
                ),
                checks=(self.name,),
            )
        return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))


class ProviderIndependenceCheck:
    """Warn when plugin source references hard-coded provider identifiers."""

    name = "provider_independence"

    def check(self, plugin: object) -> PluginCertificationResult:
        plugin_id = _plugin_id(plugin)
        haystack = _collect_plugin_strings(plugin).lower()
        warnings = tuple(
            f"Hard-coded provider reference detected: {token}"
            for token in _FORBIDDEN_PROVIDER_TOKENS
            if token in haystack
        )
        if warnings:
            return PluginCertificationResult(
                plugin_id=plugin_id,
                passed=True,
                warnings=warnings,
                checks=(self.name,),
            )
        return PluginCertificationResult.pass_result(plugin_id, checks=(self.name,))


def _collect_plugin_strings(plugin: object) -> str:
    parts: list[str] = []
    try:
        parts.append(inspect.getsource(plugin.__class__))
    except (TypeError, OSError):
        pass
    doc = plugin.__class__.__doc__
    if doc:
        parts.append(str(doc))
    return "\n".join(parts)
