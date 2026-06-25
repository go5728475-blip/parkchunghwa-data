"""Warning fixture plugin referencing openai."""

from sdk import BaseModule


class Module(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            name="warning",
            version="1.0.0",
            capabilities=("warning.analysis",),
        )

    def execute(self) -> str:
        return "openai client placeholder"
