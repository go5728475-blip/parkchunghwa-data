"""JSON-backed registry audit store."""

from __future__ import annotations

import json
from pathlib import Path

from core.plugins.registry.audit import RegistryAuditEntry


class JsonRegistryAuditStore:
    """Persists registry audit entries to a JSON file."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def append(self, entry: RegistryAuditEntry) -> None:
        data = self._read_data()
        entries = data.setdefault("entries", [])
        if not isinstance(entries, list):
            raise ValueError("registry audit entries field must be an array")
        entries.append(_entry_to_dict(entry))
        data["entries"] = entries
        self._write_data(data)

    def load_all(self) -> tuple[RegistryAuditEntry, ...]:
        entries = self._read_data().get("entries", [])
        if not isinstance(entries, list):
            raise ValueError("registry audit entries field must be an array")
        return tuple(_entry_from_dict(item) for item in entries)

    def clear(self) -> None:
        self._write_data({"entries": []})

    def _read_data(self) -> dict[str, object]:
        if not self._path.exists():
            return {"entries": []}
        raw = self._path.read_text(encoding="utf-8").strip()
        if not raw:
            return {"entries": []}
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("registry audit file must contain a JSON object")
        entries = data.get("entries")
        if entries is None:
            return {"entries": []}
        if not isinstance(entries, list):
            raise ValueError("registry audit entries field must be an array")
        return data

    def _write_data(self, data: dict[str, object]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps(data, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _entry_to_dict(entry: RegistryAuditEntry) -> dict[str, str]:
    return {
        "timestamp": entry.timestamp,
        "action": entry.action,
        "plugin_id": entry.plugin_id,
        "version": entry.version,
        "result": entry.result,
    }


def _entry_from_dict(data: dict[str, object]) -> RegistryAuditEntry:
    return RegistryAuditEntry(
        timestamp=str(data["timestamp"]),
        action=str(data["action"]),
        plugin_id=str(data["plugin_id"]),
        version=str(data["version"]),
        result=str(data["result"]),
    )
