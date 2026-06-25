"""Import tests for core interfaces and contracts."""

from __future__ import annotations

import importlib
import pkgutil

import pytest

INTERFACE_MODULES = [
    "core.interfaces.engine",
    "core.interfaces.provider",
    "core.interfaces.repository",
    "core.interfaces.service",
    "core.interfaces.command_handler",
    "core.interfaces.query_handler",
    "core.interfaces.event",
    "core.interfaces.event_store",
    "core.interfaces.event_publisher",
    "core.interfaces.unit_of_work",
]

CONTRACT_MODULES = [
    "core.contracts.base",
    "core.contracts.metadata",
    "core.contracts.request",
    "core.contracts.response",
    "core.contracts.explanation",
    "core.contracts.pagination",
    "core.contracts.error",
    "core.contracts.command",
    "core.contracts.query",
]

INTERFACE_EXPORTS = {
    "core.interfaces": [
        "IEngine",
        "IProvider",
        "IRepository",
        "IService",
        "ICommandHandler",
        "IQueryHandler",
        "IEvent",
        "IEventStore",
        "IEventPublisher",
        "IUnitOfWork",
    ],
}

CONTRACT_EXPORTS = {
    "core.contracts": [
        "Contract",
        "Metadata",
        "Request",
        "Response",
        "Explanation",
        "Pagination",
        "Error",
        "ErrorDetail",
        "Command",
        "Query",
    ],
}


@pytest.mark.parametrize("module_name", INTERFACE_MODULES)
def test_interface_module_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize("module_name", CONTRACT_MODULES)
def test_contract_module_imports(module_name: str) -> None:
    module = importlib.import_module(module_name)
    assert module is not None


@pytest.mark.parametrize(
    ("package_name", "symbols"),
    [
        ("core.interfaces", INTERFACE_EXPORTS["core.interfaces"]),
        ("core.contracts", CONTRACT_EXPORTS["core.contracts"]),
    ],
)
def test_package_exports(package_name: str, symbols: list[str]) -> None:
    package = importlib.import_module(package_name)
    for symbol in symbols:
        assert hasattr(package, symbol), f"{package_name} missing export: {symbol}"


def test_all_interface_submodules_discoverable() -> None:
    package = importlib.import_module("core.interfaces")
    discovered = {
        module_name
        for _, module_name, _ in pkgutil.iter_modules(package.__path__)
        if not module_name.startswith("_")
    }
    expected = {name.split(".")[-1] for name in INTERFACE_MODULES}
    assert expected.issubset(discovered)


def test_all_contract_submodules_discoverable() -> None:
    package = importlib.import_module("core.contracts")
    discovered = {
        module_name
        for _, module_name, _ in pkgutil.iter_modules(package.__path__)
        if not module_name.startswith("_")
    }
    expected = {name.split(".")[-1] for name in CONTRACT_MODULES}
    assert expected.issubset(discovered)
