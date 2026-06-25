"""Container errors."""


class ContainerError(Exception):
    """Raised when container resolution fails."""


class CircularDependencyError(ContainerError):
    """Raised when a circular dependency is detected during resolution."""

    def __init__(self, chain: tuple[str, ...]) -> None:
        self.chain = chain
        path = " -> ".join(chain)
        msg = f"Circular dependency detected: {path}"
        super().__init__(msg)
