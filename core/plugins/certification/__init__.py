"""Plugin certification framework."""

from core.plugins.certification.compatibility import map_result_to_compatibility_level
from core.plugins.certification.factory import create_default_plugin_certification_suite
from core.plugins.certification.gate import CertificationGate
from core.plugins.certification.interfaces import PluginCertificationCheck
from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.certification.load_gate import (
    PluginCertificationError,
    certify_plugin_before_load,
)
from core.plugins.certification.loading import CertificationLoadError, load_plugin_for_certification
from core.plugins.certification.policy import CertificationPolicy, PolicyResult
from core.plugins.certification.result import PluginCertificationResult
from core.plugins.certification.suite import PluginCertificationSuite

__all__ = [
    "CertificationGate",
    "CertificationLoadError",
    "CertificationPolicy",
    "PluginCertificationCheck",
    "PluginCertificationError",
    "PluginCertificationResult",
    "PluginCertificationSuite",
    "PluginCompatibilityLevel",
    "PolicyResult",
    "certify_plugin_before_load",
    "create_default_plugin_certification_suite",
    "load_plugin_for_certification",
    "map_result_to_compatibility_level",
]
