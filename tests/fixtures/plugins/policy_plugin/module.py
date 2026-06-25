from sdk import BaseModule


class Module(BaseModule):
    def __init__(self) -> None:
        super().__init__(
            name="policy",
            version="1.0.0",
            capabilities=("policy.analysis",),
        )
