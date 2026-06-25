"""Runtime certification policy cache."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from core.certification.models import CertificationPolicy


@dataclass(frozen=True, kw_only=True)
class PolicyCacheEntry:
    """Cached policy entry keyed by resolved path."""

    path: str
    policy: CertificationPolicy


class RuntimePolicyCache:
    """Caches loaded certification policies by path."""

    def __init__(self) -> None:
        self._entries: dict[str, PolicyCacheEntry] = {}

    def get(self, path: str | Path) -> CertificationPolicy | None:
        key = _normalize_path(path)
        entry = self._entries.get(key)
        if entry is None:
            return None
        return entry.policy

    def put(self, path: str | Path, policy: CertificationPolicy) -> None:
        key = _normalize_path(path)
        self._entries[key] = PolicyCacheEntry(path=key, policy=policy)

    def invalidate(self, path: str | Path) -> None:
        self._entries.pop(_normalize_path(path), None)

    def reload(self, path: str | Path, loader: object) -> CertificationPolicy:
        key = _normalize_path(path)
        self.invalidate(key)
        policy = loader.load(path)
        self.put(path, policy)
        return policy

    def clear(self) -> None:
        self._entries.clear()

    def paths(self) -> tuple[str, ...]:
        return tuple(sorted(self._entries))


_default_cache = RuntimePolicyCache()


def get_default_policy_cache() -> RuntimePolicyCache:
    return _default_cache


def reset_default_policy_cache() -> None:
    _default_cache.clear()


def _normalize_path(path: str | Path) -> str:
    return str(Path(path).resolve())
