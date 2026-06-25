"""Plugin project template generator."""

from __future__ import annotations

import json
import re
from pathlib import Path

from sdk.version import PLUGIN_SDK_VERSION

_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def create_plugin_template(path: str | Path) -> Path:
    """Create a plugin package template at the given path."""
    package_dir = Path(path).resolve()
    if package_dir.exists() and any(package_dir.iterdir()):
        msg = f"Target path is not empty: {package_dir}"
        raise ValueError(msg)

    plugin_name = package_dir.name
    if not _NAME_PATTERN.match(plugin_name):
        msg = f"Invalid plugin directory name: {plugin_name}"
        raise ValueError(msg)

    capability = f"{plugin_name}.analysis"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "tests").mkdir(exist_ok=True)

    (package_dir / "manifest.json").write_text(
        json.dumps(
            {
                "name": plugin_name,
                "version": "0.1.0",
                "author": "Plugin Developer",
                "description": f"{plugin_name} analysis module",
                "capabilities": [capability],
                "module_class": "Module",
                "sdk_version": PLUGIN_SDK_VERSION,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (package_dir / "module.py").write_text(
        _MODULE_TEMPLATE.format(
            plugin_name=plugin_name,
            capability=capability,
        ),
        encoding="utf-8",
    )
    (package_dir / "README.md").write_text(
        _README_TEMPLATE.format(
            plugin_name=plugin_name,
            capability=capability,
        ),
        encoding="utf-8",
    )
    (package_dir / "requirements.txt").write_text(
        "# Add external dependencies for this plugin package.\n",
        encoding="utf-8",
    )
    (package_dir / "tests" / "test_module.py").write_text(
        _TEST_TEMPLATE.format(plugin_name=plugin_name),
        encoding="utf-8",
    )
    (package_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")

    return package_dir


_MODULE_TEMPLATE = '''"""{plugin_name} module package."""

from __future__ import annotations

from sdk import BaseModule


class Module(BaseModule):
    """MASTER ENGINE module for {plugin_name}."""

    def __init__(self) -> None:
        super().__init__(
            name="{plugin_name}",
            version="0.1.0",
            author="Plugin Developer",
            description="{plugin_name} analysis module",
            capabilities=("{capability}",),
        )
'''

_README_TEMPLATE = """# {plugin_name}

MASTER ENGINE plugin package.

## Capabilities

- `{capability}`

## Development

```bash
python -m core.cli.main validate-plugin ./{plugin_name}
python -m core.cli.main load-module ./{plugin_name}
```
"""

_TEST_TEMPLATE = '''"""Tests for {plugin_name} module."""

from module import Module


def test_module_metadata() -> None:
    module = Module()

    assert module.name() == "{plugin_name}"
    assert module.version() == "0.1.0"
    assert module.capabilities() == ("{plugin_name}.analysis",)
'''
