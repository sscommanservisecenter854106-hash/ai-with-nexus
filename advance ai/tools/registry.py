from typing import Dict, List, Optional
from .base import BaseTool

class ToolRegistry:
    _tools: Dict[str, BaseTool] = {}

    @classmethod
    def register(cls, tool_instance: BaseTool):
        cls._tools[tool_instance.name] = tool_instance
        return tool_instance

    @classmethod
    def get(cls, name: str) -> Optional[BaseTool]:
        return cls._tools.get(name)

    @classmethod
    def list_all(cls) -> List[BaseTool]:
        return list(cls._tools.values())

    @classmethod
    def get_schemas(cls, enabled_names: Optional[List[str]] = None) -> List[dict]:
        tools = cls.list_all()
        if enabled_names is not None:
            tools = [t for t in tools if t.name in enabled_names]
        return [t.to_schema() for t in tools]

    @classmethod
    async def execute(cls, name: str, **kwargs) -> str:
        tool = cls.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found."
        try:
            return await tool.run(**kwargs)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"

def register_tool(cls):
    instance = cls()
    ToolRegistry.register(instance)
    return cls
