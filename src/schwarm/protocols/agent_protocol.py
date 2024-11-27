from typing import Literal, Protocol

from schwarm.provider.base.base_provider import BaseProviderConfig


class AgentProtocol(Protocol):
    """Protocol for agent implementations."""

    name: str
    model: str
    description: str
    instructions: str
    functions: list[str]
    tool_choice: Literal["none", "auto", "required"]
    parallel_tool_calls: bool
    provider_configurations: list[BaseProviderConfig]
