"""Defines the context available to providers."""

from typing import Any

from pydantic import BaseModel, Field

from schwarm.models.message import Message
from schwarm.models.types import Agent, AgentFunction


class ProviderContext(BaseModel):
    """Context available to providers.

    This class encapsulates all the data that providers might need access to,
    including message history, available agents, tools, and other providers.
    """

    message_history: list[Message] = Field(
        default_factory=list, description="History of all messages in the current conversation"
    )
    current_message: Message | None = Field(..., description="The current message being processed")
    current_agent: Agent = Field(..., description="The agent currently using this provider")
    available_agents: list[Agent] = Field(default_factory=list, description="Map of all available agents by name")
    available_tools: list[AgentFunction] = Field(
        default_factory=list, description="List of all available tools/functions"
    )
    available_providers: dict[str, Any] = Field(
        default_factory=dict, description="Map of all available providers by name"
    )
    context_variables: dict[str, Any] = Field(default_factory=dict, description="Current context variables")
    current_instruction: str | None = Field(default=None, description="Current instruction being processed")
