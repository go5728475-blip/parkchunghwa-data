"""Builtin engine module base."""

from __future__ import annotations

from core.container.interfaces import IContainer
from core.modules.interfaces import IModule
from core.modules.models import ModuleDescriptor


class BuiltinModuleBase(IModule):
    """Shared stub implementation for builtin engine modules."""

    def __init__(
        self,
        *,
        module_name: str,
        version: str,
        capabilities: tuple[str, ...],
    ) -> None:
        self._module_name = module_name
        self._version = version
        self._capabilities = capabilities
        self._loaded = False

    def name(self) -> str:
        return self._module_name

    def version(self) -> str:
        return self._version

    def capabilities(self) -> tuple[str, ...]:
        return self._capabilities

    def register(self, container: IContainer) -> None:
        container.register_singleton(
            self._descriptor_key(),
            ModuleDescriptor(
                name=self._module_name,
                version=self._version,
                capabilities=self._capabilities,
                loaded=False,
            ),
        )

    def boot(self, container: IContainer) -> None:
        self._loaded = True
        container.register_singleton(
            self._descriptor_key(),
            ModuleDescriptor(
                name=self._module_name,
                version=self._version,
                capabilities=self._capabilities,
                loaded=True,
            ),
        )

    def shutdown(self, container: IContainer) -> None:
        self._loaded = False
        container.register_singleton(
            self._descriptor_key(),
            ModuleDescriptor(
                name=self._module_name,
                version=self._version,
                capabilities=self._capabilities,
                loaded=False,
            ),
        )

    def _descriptor_key(self) -> str:
        return f"module.{self._module_name}"
