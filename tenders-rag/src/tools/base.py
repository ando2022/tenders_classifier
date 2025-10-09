from typing import Protocol


class Tool(Protocol):
    name: str
    def run(self, kwargs) -> dict: ...
    # description of the input in JSON for the model to know how to call the tool
    def schema(self): ...
