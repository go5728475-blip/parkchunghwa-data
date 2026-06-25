"""Certification policy errors."""


class PolicyLoadError(Exception):
    """Raised when a policy file cannot be loaded."""


class PolicyValidationError(Exception):
    """Raised when policy validation fails."""

    def __init__(self, message: str, *, errors: tuple[str, ...] = ()) -> None:
        super().__init__(message)
        self.errors = errors
