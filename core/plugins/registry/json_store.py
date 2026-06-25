"""JSON-backed certified plugin registry store."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from core.plugins.certification.levels import PluginCompatibilityLevel
from core.plugins.registry.certified import CertifiedPluginRecord


class JsonCertifiedPluginRegistryStore:
    """Persists certified plugin records to a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def save(self, record: CertifiedPluginRecord) -> None:
        data = self._read_data()
        plugins = data.setdefault("plugins", {})
        plugins[record.plugin_id] = _record_to_dict(record)
        self._write_data(data)

    def load(self, plugin_id: str) -> CertifiedPluginRecord | None:
        plugin_data = self._read_data().get("plugins", {}).get(plugin_id)
        if plugin_data is None:
            return None
        return _record_from_dict(plugin_data)

    def load_all(self) -> tuple[CertifiedPluginRecord, ...]:
        plugins = self._read_data().get("plugins", {})
        plugin_ids = sorted(plugins)
        return tuple(_record_from_dict(plugins[plugin_id]) for plugin_id in plugin_ids)

    def delete(self, plugin_id: str) -> None:
        data = self._read_data()
        plugins = data.get("plugins", {})
        if plugin_id not in plugins:
            return
        del plugins[plugin_id]
        data["plugins"] = plugins
        self._write_data(data)

    def _read_data(self) -> dict[str, object]:
        if not self._path.exists():
            return {"plugins": {}}
        raw = self._path.read_text(encoding="utf-8").strip()
        if not raw:
            return {"plugins": {}}
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("certified plugin registry file must contain a JSON object")
        plugins = data.get("plugins")
        if plugins is None:
            return {"plugins": {}}
        if not isinstance(plugins, dict):
            raise ValueError("certified plugin registry plugins field must be an object")
        return data

    def _write_data(self, data: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _record_to_dict(record: CertifiedPluginRecord) -> dict[str, object]:
    return {
        "plugin_id": record.plugin_id,
        "version": record.version,
        "compatibility_level": record.compatibility_level.value,
        "certified": record.certified,
        "warnings": list(record.warnings),
        "checks": list(record.checks),
        "certified_at": record.certified_at.astimezone(UTC).isoformat(),
    }


def _record_from_dict(data: dict[str, object]) -> CertifiedPluginRecord:
    compatibility_raw = data.get("compatibility_level", PluginCompatibilityLevel.UNKNOWN.value)
    warnings_raw = data.get("warnings", [])
    checks_raw = data.get("checks", [])
    certified_at_raw = data.get("certified_at")
    if certified_at_raw is None:
        certified_at = datetime.now(UTC)
    else:
        certified_at = datetime.fromisoformat(str(certified_at_raw))
        if certified_at.tzinfo is None:
            certified_at = certified_at.replace(tzinfo=UTC)
        else:
            certified_at = certified_at.astimezone(UTC)
    return CertifiedPluginRecord(
        plugin_id=str(data["plugin_id"]),
        version=str(data["version"]),
        compatibility_level=PluginCompatibilityLevel(str(compatibility_raw)),
        certified=bool(data["certified"]),
        warnings=tuple(str(item) for item in warnings_raw),
        checks=tuple(str(item) for item in checks_raw),
        certified_at=certified_at,
    )
