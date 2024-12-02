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
    breakpoint_counter: int = Field(default=0, description="Current turn in the conversation")
    override_model: str | None = Field(default=None, description="Model override for the current conversation")
    message_history: list[Message] = Field(
        default_factory=list, description="History of all messages in the current conversation"
    )
    current_message: Message | None = Field(default=None, description="The current message being processed")
    default_handoff_agent: Any = Field(default=None, description="The agent currently using this provider")
    current_agent: Any = Field(default=None, description="The agent currently using this provider")  # TODO str?
    previous_agent: Any = Field(default=None, description="The agent currently using this provider")  # TODO str?
    available_agents: list[Any] = Field(default_factory=list, description="Map of all available agents by name")
    available_tools: list[Any] = Field(default_factory=list, description="List of all available tools/functions")
    current_tools: list[Any] | None = Field(
        default=None, description="The tool currently chosen by the agent"
    )  # TODO str?
    current_tool_result: Any = Field(default=None, description="The result of the tool currently chosen by the agent")
    available_providers: list[Any] = Field(default_factory=list, description="L of all available providers by name")
    context_variables: dict[str, Any] = Field(default_factory=dict, description="Current context variables")
    instruction_func: Any = Field(default=None, description="Current instruction being processed (always text)")
    instruction_str: str | None = Field(default=None, description="Resolved instruction (always text)")
    token_spent: int = Field(default=0, description="Number of tokens spent in the current conversation")
    token_cost: float = Field(default=0, description="Number of tokens spent in the current conversation")
    streamed_output: str | None = Field(default=None, description="Streamed output from the provider")
    model_config = {"arbitrary_types_allowed": True}
