from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseTool(ABC):
    name: str = ""
    description: str = ""
    parameters: Dict[str, Any] = {}

    @abstractmethod
    async def run(self, **kwargs) -> str:
        """Execute the tool asynchronously and return a string result."""
        pass

    def to_schema(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
