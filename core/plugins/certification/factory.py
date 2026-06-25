"""Plugin certification factory."""

from __future__ import annotations

from core.plugins.certification.checks import (
    CapabilityDeclarationCheck,
    LifecycleCheck,
    ManifestRequiredCheck,
    ProviderIndependenceCheck,
    SDKVersionCheck,
)
from core.plugins.certification.suite import PluginCertificationSuite


def create_default_plugin_certification_suite() -> PluginCertificationSuite:
    """Create a suite with all built-in certification checks."""
    suite = PluginCertificationSuite()
    suite.register_check(ManifestRequiredCheck())
    suite.register_check(LifecycleCheck())
    suite.register_check(CapabilityDeclarationCheck())
    suite.register_check(SDKVersionCheck())
    suite.register_check(ProviderIndependenceCheck())
    return suite
