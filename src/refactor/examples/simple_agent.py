"""Example of using the refactored agent system."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from ..core.agent import Agent
from ..core.orchestrator import Orchestrator
from ..core.types import AgentConfig


def search_web(query: str) -> str:
    """Simulated web search tool."""
    return f"Found results for: {query}"


def calculate(expression: str) -> str:
    """Simple calculator tool."""
    try:
        result = eval(expression, {"__builtins__": {}})  # Safely evaluate math expressions
        return str(result)
    except Exception as e:
        return f"Error calculating {expression}: {e!s}"


@dataclass
class SimpleTool:
    """A simple tool implementation."""

    name: str
    description: str
    func: Callable[..., Any]
    parameters: dict[str, Any] = field(
        default_factory=lambda: {
            "type": "object",
            "properties": {"input": {"type": "string", "description": "Input for the tool"}},
            "required": ["input"],
        }
    )

    def __call__(self, **kwargs: Any) -> Any:
        """Execute the tool."""
        return self.func(**kwargs)


def main():
    """Run a simple agent example."""
    # Create tools
    search_tool = SimpleTool(name="search", description="Search the web for information", func=search_web)

    calculator_tool = SimpleTool(name="calculate", description="Calculate mathematical expressions", func=calculate)

    # Create agent config
    config = AgentConfig(
        model="gpt-3.5-turbo",
        api_key="your-api-key-here",  # Replace with actual API key
        temperature=0.7,
    )

    # Create agent
    agent = Agent(
        name="Assistant",
        description="A helpful assistant that can search and calculate",
        config=config,
        tools=[search_tool, calculator_tool],
        instructions="""You are a helpful assistant that can search the web and perform calculations.
        When asked about facts, use the search tool.
        When asked to calculate something, use the calculate tool.""",
    )

    # Create orchestrator
    orchestrator = Orchestrator()

    # Run a conversation
    result = orchestrator.run_single_turn(agent=agent, message="What is 2 + 2 and who is Albert Einstein?", context={})

    # Print results
    print("\nConversation:")
    for msg in result.messages:
        print(f"\n{msg.role.upper()}: {msg.content}")
        if msg.tool_calls:
            print(f"Tool calls: {json.dumps(msg.tool_calls, indent=2)}")


if __name__ == "__main__":
    main()
