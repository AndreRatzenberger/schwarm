"""Defines the context available to providers."""

from typing import Any

from pydantic import BaseModel, Field, model_validator

from schwarm.models.message import Message


class ProviderContext(BaseModel):
    """Context available to providers.

    This class encapsulates all the data that providers might need access to,
    including message history, available agents, tools, and other providers.
    """

    message_history: list[Message] = Field(
        default_factory=list, description="History of all messages in the current conversation"
    )
    current_message: Message | None = Field(..., description="The current message being processed")
    current_agent: Any = Field(..., description="The agent currently using this provider")
    available_agents: list[Any] = Field(default_factory=list, description="Map of all available agents by name")
    available_tools: list[Any] = Field(default_factory=list, description="List of all available tools/functions")
    available_providers: dict[str, Any] = Field(
        default_factory=dict, description="Map of all available providers by name"
    )
    context_variables: dict[str, Any] = Field(default_factory=dict, description="Current context variables")
    current_instruction: str | None = Field(default=None, description="Current instruction being processed")

    model_config = {"arbitrary_types_allowed": True}

    @model_validator(mode="after")
    def validate_agent_types(self) -> "ProviderContext":
        """Validate that agent types are correct."""
        from schwarm.models.agent import Agent

        if not isinstance(self.current_agent, Agent):
            raise ValueError("current_agent must be an Agent instance")

        if not all(isinstance(agent, Agent) for agent in self.available_agents):
            raise ValueError("all available_agents must be Agent instances")

        if self.current_message is not None and not isinstance(self.current_message, Message):
            raise ValueError("current_message must be a Message instance")

        if not all(isinstance(msg, Message) for msg in self.message_history):
            raise ValueError("all message_history items must be Message instances")

        return self
