"""Base model for provider context."""

from typing import Any

from pydantic import BaseModel, Field

from schwarm.models.message import Message


class ProviderContextModel(BaseModel):
    """Base model for context available to providers.

    This class defines the data structure that providers might need access to,
    including message history, available agents, tools, and other providers.

    ProviderContextModel has to be serializable to JSON
    """

    max_turns: int = Field(default=10, description="Maximum number of turns in a conversation")
    current_turn: int = Field(default=0, description="Current turn in the conversation")
    model_override: str | None = Field(default=None, description="Model override for the current conversation")
    message_history: list[Message] = Field(
        default_factory=list, description="History of all messages in the current conversation"
    )
    current_message: Message | None = Field(default=None, description="The current message being processed")
    current_agent: Any = Field(default=None, description="The agent currently using this provider")  # TODO str?
    available_agents: list[Any] = Field(default_factory=list, description="Map of all available agents by name")
    available_tools: list[Any] = Field(default_factory=list, description="List of all available tools/functions")
    available_providers: dict[str, Any] = Field(
        default_factory=dict, description="Map of all available providers by name"
    )
    context_variables: dict[str, Any] = Field(default_factory=dict, description="Current context variables")
    instruction_func: Any = Field(default=None, description="Current instruction being processed (always text)")
    instruction_str: str | None = Field(default=None, description="Resolved instruction (always text)")
    model_config = {"arbitrary_types_allowed": True}
