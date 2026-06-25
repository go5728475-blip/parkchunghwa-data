"""Tests for persistent certified plugin registry."""

from __future__ import annotations

from pathlib import Path

import pytest

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.certified import CertifiedPluginRecord, CertifiedPluginRegistry
from core.plugins.registry.json_store import JsonCertifiedPluginRegistryStore


def _record(
    *,
    plugin_id: str,
    version: str = "1.0.0",
    compatibility_level: PluginCompatibilityLevel = PluginCompatibilityLevel.COMPATIBLE,
    certified: bool = True,
    warnings: tuple[str, ...] = (),
    checks: tuple[str, ...] = ("manifest_required",),
) -> CertifiedPluginRecord:
    return CertifiedPluginRecord(
        plugin_id=plugin_id,
        version=version,
        compatibility_level=compatibility_level,
        certified=certified,
        warnings=warnings,
        checks=checks,
    )


def test_json_store_saves_record(tmp_path: Path) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    record = _record(plugin_id="wealth")

    store.save(record)

    assert (tmp_path / "registry.json").exists()
    assert store.load("wealth") == record


def test_json_store_loads_record(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    registry_path.write_text(
        """
{
  "plugins": {
    "career": {
      "plugin_id": "career",
      "version": "0.2.0",
      "compatibility_level": "PARTIAL",
      "certified": true,
      "warnings": ["provider warning"],
      "checks": ["manifest_required"]
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    store = JsonCertifiedPluginRegistryStore(registry_path)

    record = store.load("career")

    assert record is not None
    assert record.plugin_id == "career"
    assert record.version == "0.2.0"
    assert record.compatibility_level == PluginCompatibilityLevel.PARTIAL
    assert record.warnings == ("provider warning",)


def test_json_store_load_all(tmp_path: Path) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    store.save(_record(plugin_id="wealth"))
    store.save(
        _record(
            plugin_id="career",
            compatibility_level=PluginCompatibilityLevel.PARTIAL,
        ),
    )

    records = store.load_all()

    assert [record.plugin_id for record in records] == ["career", "wealth"]


def test_json_store_delete(tmp_path: Path) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    store.save(_record(plugin_id="health"))
    store.save(_record(plugin_id="study"))

    store.delete("health")

    assert store.load("health") is None
    assert [record.plugin_id for record in store.load_all()] == ["study"]


def test_registry_loads_from_store_on_init(tmp_path: Path) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    store.save(_record(plugin_id="relationship"))

    registry = CertifiedPluginRegistry(store=store)

    assert registry.get("relationship") is not None
    assert registry.list_all()[0].plugin_id == "relationship"


def test_registry_register_persists_to_store(tmp_path: Path) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    registry = CertifiedPluginRegistry(store=store)

    registry.register(_record(plugin_id="study", version="0.3.0"))

    assert store.load("study") is not None
    assert store.load("study").version == "0.3.0"


def test_registry_delete_persists_to_store(tmp_path: Path) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    registry = CertifiedPluginRegistry(store=store)
    registry.register(_record(plugin_id="health"))

    registry.delete("health")

    assert registry.get("health") is None
    assert store.load("health") is None


@pytest.mark.parametrize(
    ("level",),
    [
        (PluginCompatibilityLevel.UNKNOWN,),
        (PluginCompatibilityLevel.COMPATIBLE,),
        (PluginCompatibilityLevel.PARTIAL,),
        (PluginCompatibilityLevel.INCOMPATIBLE,),
    ],
)
def test_compatibility_level_serialization_roundtrip(
    tmp_path: Path,
    level: PluginCompatibilityLevel,
) -> None:
    store = JsonCertifiedPluginRegistryStore(tmp_path / "registry.json")
    record = _record(
        plugin_id="wealth",
        compatibility_level=level,
        certified=level != PluginCompatibilityLevel.INCOMPATIBLE,
    )

    store.save(record)
    loaded = store.load("wealth")

    assert loaded is not None
    assert loaded.compatibility_level == level
