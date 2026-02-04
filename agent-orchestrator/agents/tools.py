from dataclasses import dataclass
from typing import Any, Callable, Dict


@dataclass(frozen=True)
class Tool:
    name: str
    handler: Callable[[Dict[str, Any]], str]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def validate(self, tool_name: str) -> None:
        if tool_name not in self._tools:
            raise ValueError(f"Tool '{tool_name}' is not registered")

    def call(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        self.validate(tool_name)
        return self._tools[tool_name].handler(arguments)


registry = ToolRegistry()


def _echo_tool(arguments: Dict[str, Any]) -> str:
    return f"echo:{arguments.get('text', '')}"


def _math_tool(arguments: Dict[str, Any]) -> str:
    expression = arguments.get("expression", "0")
    try:
        result = eval(expression, {"__builtins__": {}}, {})
    except Exception as exc:
        raise ValueError(f"Invalid expression: {expression}") from exc
    return str(result)


registry.register(Tool(name="echo", handler=_echo_tool))
registry.register(Tool(name="calculator", handler=_math_tool))
