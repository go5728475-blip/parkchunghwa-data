"""Provider error types."""

from __future__ import annotations


class ProviderError(Exception):
    """Base provider error."""


class ProviderNotFoundError(ProviderError):
    """Raised when a provider cannot be found."""


class DuplicateProviderError(ProviderError):
    """Raised when registering the same provider twice."""


class ProviderGenerationError(ProviderError):
    """Raised when provider generation fails or is not allowed."""
