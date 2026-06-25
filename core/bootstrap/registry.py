"""Application component registry."""

from __future__ import annotations

from typing import Any


class RegistryError(Exception):
    """Raised when registry operations fail."""


class DuplicateRegistrationError(RegistryError):
    """Raised when registering the same key twice."""


class Registry:
    """Typed registry for handlers, repositories, services, and use cases."""

    def __init__(self) -> None:
        self._command_handlers: dict[type[Any], Any] = {}
        self._query_handlers: dict[type[Any], Any] = {}
        self._repositories: dict[str, Any] = {}
        self._services: dict[str, Any] = {}
        self._event_publishers: dict[str, Any] = {}
        self._event_stores: dict[str, Any] = {}
        self._use_cases: dict[str, Any] = {}

    def register_command_handler(self, command_type: type[Any], handler: Any) -> None:
        """Register a command handler for a command type."""
        self._ensure_unique("command handler", command_type.__name__, command_type in self._command_handlers)
        self._command_handlers[command_type] = handler

    def get_command_handler(self, command_type: type[Any]) -> Any:
        """Return a registered command handler."""
        return self._require("command handler", command_type.__name__, self._command_handlers.get(command_type))

    def has_command_handler(self, command_type: type[Any]) -> bool:
        return command_type in self._command_handlers

    def register_query_handler(self, query_type: type[Any], handler: Any) -> None:
        """Register a query handler for a query type."""
        self._ensure_unique("query handler", query_type.__name__, query_type in self._query_handlers)
        self._query_handlers[query_type] = handler

    def get_query_handler(self, query_type: type[Any]) -> Any:
        """Return a registered query handler."""
        return self._require("query handler", query_type.__name__, self._query_handlers.get(query_type))

    def has_query_handler(self, query_type: type[Any]) -> bool:
        return query_type in self._query_handlers

    def register_repository(self, name: str, repository: Any) -> None:
        """Register a repository by name."""
        self._ensure_unique("repository", name, name in self._repositories)
        self._repositories[name] = repository

    def get_repository(self, name: str) -> Any:
        """Return a registered repository."""
        return self._require("repository", name, self._repositories.get(name))

    def has_repository(self, name: str) -> bool:
        return name in self._repositories

    def register_service(self, name: str, service: Any) -> None:
        """Register a service by name."""
        self._ensure_unique("service", name, name in self._services)
        self._services[name] = service

    def get_service(self, name: str) -> Any:
        """Return a registered service."""
        return self._require("service", name, self._services.get(name))

    def has_service(self, name: str) -> bool:
        return name in self._services

    def register_event_publisher(self, name: str, publisher: Any) -> None:
        """Register an event publisher by name."""
        self._ensure_unique("event publisher", name, name in self._event_publishers)
        self._event_publishers[name] = publisher

    def get_event_publisher(self, name: str) -> Any:
        """Return a registered event publisher."""
        return self._require("event publisher", name, self._event_publishers.get(name))

    def has_event_publisher(self, name: str) -> bool:
        return name in self._event_publishers

    def register_event_store(self, name: str, store: Any) -> None:
        """Register an event store by name."""
        self._ensure_unique("event store", name, name in self._event_stores)
        self._event_stores[name] = store

    def get_event_store(self, name: str) -> Any:
        """Return a registered event store."""
        return self._require("event store", name, self._event_stores.get(name))

    def has_event_store(self, name: str) -> bool:
        return name in self._event_stores

    def register_use_case(self, name: str, use_case: Any) -> None:
        """Register a use case by name."""
        self._ensure_unique("use case", name, name in self._use_cases)
        self._use_cases[name] = use_case

    def get_use_case(self, name: str) -> Any:
        """Return a registered use case."""
        return self._require("use case", name, self._use_cases.get(name))

    def has_use_case(self, name: str) -> bool:
        return name in self._use_cases

    def command_handlers(self) -> dict[type[Any], Any]:
        return dict(self._command_handlers)

    def query_handlers(self) -> dict[type[Any], Any]:
        return dict(self._query_handlers)

    def clear(self) -> None:
        """Remove all registrations."""
        self._command_handlers.clear()
        self._query_handlers.clear()
        self._repositories.clear()
        self._services.clear()
        self._event_publishers.clear()
        self._event_stores.clear()
        self._use_cases.clear()

    @staticmethod
    def _ensure_unique(kind: str, name: str, exists: bool) -> None:
        if exists:
            msg = f"Duplicate {kind} registration: {name}"
            raise DuplicateRegistrationError(msg)

    @staticmethod
    def _require(kind: str, name: str, value: Any) -> Any:
        if value is None:
            msg = f"{kind.title()} not registered: {name}"
            raise RegistryError(msg)
        return value
