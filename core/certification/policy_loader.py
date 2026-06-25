"""Certification policy loading."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from pathlib import Path

from core.certification.errors import PolicyLoadError
from core.certification.models import CertificationPolicy, PolicyRule

logger = logging.getLogger("certification.policy.load")


class PolicyLoaderRegistry:
    """Registry for plugin-based policy loaders keyed by file extension."""

    def __init__(self) -> None:
        self._loaders: dict[str, Callable[[str], dict[str, object]]] = {}

    def register(
        self,
        extension: str,
        loader: Callable[[str], dict[str, object]],
    ) -> None:
        normalized = extension.lower()
        if not normalized.startswith("."):
            normalized = f".{normalized}"
        self._loaders[normalized] = loader

    def resolve(self, path: str | Path) -> Callable[[str], dict[str, object]]:
        extension = Path(path).suffix.lower()
        loader = self._loaders.get(extension)
        if loader is None:
            msg = f"No policy loader registered for extension: {extension}"
            raise PolicyLoadError(msg)
        return loader


class CertificationPolicyLoader:
    """Loads certification policies from JSON or YAML files."""

    def __init__(self, registry: PolicyLoaderRegistry | None = None) -> None:
        self._registry = registry or _default_loader_registry

    def load(self, path: str | Path) -> CertificationPolicy:
        policy_path = Path(path)
        logger.info("Loading certification policy from %s", policy_path)
        if not policy_path.exists():
            msg = f"Policy file not found: {policy_path}"
            raise PolicyLoadError(msg)
        try:
            text = policy_path.read_text(encoding="utf-8")
            loader = self._registry.resolve(policy_path)
            raw = loader(text)
        except PolicyLoadError:
            raise
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            msg = f"Failed to load policy file: {policy_path}"
            raise PolicyLoadError(msg) from exc
        return _parse_policy(raw)


def _parse_policy(raw: object) -> CertificationPolicy:
    if not isinstance(raw, dict):
        msg = "Policy root must be a mapping"
        raise PolicyLoadError(msg)
    rules_raw = raw.get("rules", [])
    if not isinstance(rules_raw, list):
        msg = "Policy rules must be a list"
        raise PolicyLoadError(msg)
    rules: list[PolicyRule] = []
    for index, item in enumerate(rules_raw):
        if not isinstance(item, dict):
            msg = f"Rule at index {index} must be a mapping"
            raise PolicyLoadError(msg)
        rules.append(_parse_rule(item, index))
    try:
        return CertificationPolicy(
            version=str(raw["version"]),
            id=str(raw["id"]),
            name=str(raw["name"]),
            rules=tuple(rules),
        )
    except KeyError as exc:
        msg = f"Policy missing required field: {exc.args[0]}"
        raise PolicyLoadError(msg) from exc


def _parse_rule(raw: dict[str, object], index: int) -> PolicyRule:
    try:
        rule_id = str(raw["id"])
        severity = str(raw["severity"])
        actions_raw = raw["actions"]
    except KeyError as exc:
        msg = f"Rule at index {index} missing required field: {exc.args[0]}"
        raise PolicyLoadError(msg) from exc
    if not isinstance(actions_raw, list) or not actions_raw:
        msg = f"Rule {rule_id} actions must be a non-empty list"
        raise PolicyLoadError(msg)
    actions = tuple(str(action) for action in actions_raw)
    field = raw.get("field")
    forbidden = raw.get("forbidden")
    required = bool(raw.get("required", False))
    return PolicyRule(
        id=rule_id,
        severity=severity,
        actions=actions,
        field=str(field) if field is not None else None,
        required=required,
        forbidden=str(forbidden) if forbidden is not None else None,
    )


def _load_json_text(text: str) -> dict[str, object]:
    data = json.loads(text)
    if not isinstance(data, dict):
        msg = "Policy root must be a mapping"
        raise PolicyLoadError(msg)
    return data


def _load_yaml_text(text: str) -> dict[str, object]:
    try:
        import yaml  # type: ignore[import-untyped]
    except ImportError:
        data = _parse_basic_yaml(text)
    else:
        data = yaml.safe_load(text)
    if not isinstance(data, dict):
        msg = "Policy root must be a mapping"
        raise PolicyLoadError(msg)
    return data


def _parse_basic_yaml(text: str) -> dict[str, object]:
    """Parse a constrained YAML subset without external dependencies."""
    lines = text.splitlines()
    if not lines:
        return {}
    root, _ = _parse_yaml_block(lines, 0, 0)
    if not isinstance(root, dict):
        msg = "Policy root must be a mapping"
        raise PolicyLoadError(msg)
    return root


def _parse_yaml_block(
    lines: list[str],
    start: int,
    indent: int,
) -> tuple[object, int]:
    if start >= len(lines):
        return {}, start
    stripped = lines[start].strip()
    if stripped.startswith("- "):
        return _parse_yaml_list(lines, start, indent)
    result: dict[str, object] = {}
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        if current_indent > indent:
            msg = "Invalid YAML indentation"
            raise PolicyLoadError(msg)
        key, _, remainder = line.strip().partition(":")
        if not remainder:
            index += 1
            child, index = _parse_yaml_block(lines, index, indent + 2)
            result[key.strip()] = child
            continue
        value_text = remainder.strip()
        if not value_text:
            index += 1
            child, index = _parse_yaml_block(lines, index, indent + 2)
            result[key.strip()] = child
            continue
        result[key.strip()] = _parse_yaml_scalar(value_text)
        index += 1
    return result, index


def _parse_yaml_list(lines: list[str], start: int, indent: int) -> tuple[list[object], int]:
    items: list[object] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if not line.strip() or line.strip().startswith("#"):
            index += 1
            continue
        current_indent = len(line) - len(line.lstrip(" "))
        if current_indent < indent:
            break
        stripped = line.strip()
        if not stripped.startswith("- "):
            break
        remainder = stripped[2:].strip()
        if remainder and ":" in remainder and not remainder.startswith('"'):
            key, _, value = remainder.partition(":")
            if value.strip():
                item = {key.strip(): _parse_yaml_scalar(value.strip())}
                index += 1
                while index < len(lines):
                    nested = lines[index]
                    if not nested.strip():
                        index += 1
                        continue
                    nested_indent = len(nested) - len(nested.lstrip(" "))
                    if nested_indent <= current_indent:
                        break
                    nested_key, _, nested_value = nested.strip().partition(":")
                    if nested_value.strip():
                        item[nested_key.strip()] = _parse_yaml_scalar(nested_value.strip())
                    else:
                        child, index = _parse_yaml_block(lines, index + 1, nested_indent + 2)
                        item[nested_key.strip()] = child
                        continue
                    index += 1
                items.append(item)
                continue
            item: dict[str, object] = {}
            item[key.strip()] = _parse_yaml_scalar(value.strip()) if value.strip() else None
            index += 1
            while index < len(lines):
                nested = lines[index]
                if not nested.strip():
                    index += 1
                    continue
                nested_indent = len(nested) - len(nested.lstrip(" "))
                if nested_indent <= current_indent:
                    break
                nested_key, _, nested_value = nested.strip().partition(":")
                if not nested_value.strip():
                    child, index = _parse_yaml_block(lines, index + 1, nested_indent + 2)
                    item[nested_key.strip()] = child
                    continue
                item[nested_key.strip()] = _parse_yaml_scalar(nested_value.strip())
                index += 1
            items.append(item)
            continue
        if remainder:
            items.append(_parse_yaml_scalar(remainder))
            index += 1
            continue
        index += 1
        child, index = _parse_yaml_block(lines, index, current_indent + 2)
        items.append(child)
    return items, index


def _parse_yaml_scalar(value: str) -> object:
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return value


_default_loader_registry = PolicyLoaderRegistry()
_default_loader_registry.register(".json", _load_json_text)
_default_loader_registry.register(".yaml", _load_yaml_text)
_default_loader_registry.register(".yml", _load_yaml_text)
