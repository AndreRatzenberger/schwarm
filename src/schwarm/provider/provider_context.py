"""Defines the context available to providers."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from schwarm.models.message import Message


class ProviderContext(BaseModel):
    """Context available to providers.

    This class encapsulates all the data that providers might need access to,
    including message history, available agents, tools, and other providers.

    ProviderContext has to be serializable to JSON
    """

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
    instruction_func: Callable[..., str] | None = Field(
        default=None, description="Current instruction being processed (always text)"
    )
    instruction_str: str | None = Field(default=None, description="Resolved instruction (always text)")
    model_config = {"arbitrary_types_allowed": True}
