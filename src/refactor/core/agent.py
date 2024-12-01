"""Core agent functionality."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel

from .types import AgentConfig, Message, Tool


class Agent(BaseModel):
    """An agent that can engage in conversations and use tools."""

    name: str
    description: str
    config: AgentConfig
    tools: list[Tool] = []
    instructions: str | Callable[[dict[str, Any]], str] = "You are a helpful assistant."

    def get_system_message(self, context: dict[str, Any]) -> Message:
        """Get the system message for this agent."""
        if callable(self.instructions):
            content = self.instructions(context)
        else:
            content = self.instructions
        return Message(content=content, role="system")

    def get_tool_descriptions(self) -> list[dict[str, Any]]:
        """Get descriptions of available tools."""
        return [
            {"name": tool.name, "description": tool.description, "parameters": getattr(tool, "parameters", {})}
            for tool in self.tools
        ]

    def execute_tool(self, tool_name: str, **kwargs: Any) -> Any:
        """Execute a tool by name."""
        for tool in self.tools:
            if tool.name == tool_name:
                return tool(**kwargs)
        raise ValueError(f"Tool {tool_name} not found")

    class Config:
        """Pydantic configuration."""

        arbitrary_types_allowed = True
