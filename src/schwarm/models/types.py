"""Defines Pydantic models for agent types and interaction results."""

from collections.abc import Callable
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field

from schwarm.models.message import Message
from schwarm.provider.litellm_provider import LiteLLMConfig
from schwarm.services.budget_service import BudgetService

# Type alias for agent functions that can return various types
AgentFunction = Callable[..., "str | Agent | dict[str, Any] | Result"]
ContextVariables = dict[str, Any]


class Agent(BaseModel):
    """Represents an AI agent with specific capabilities and configuration.

    Attributes:
        name: The name identifier for the agent
        model: The OpenAI model to use for this agent
        instructions: Static or dynamic instructions for the agent's behavior
        functions: List of callable functions available to the agent
        tool_choice: Specific tool selection strategy
        parallel_tool_calls: Whether multiple tools can be called simultaneously
    """

    name: str = Field(default="Agent", description="Identifier name for the agent")
    model: str = Field(default="gpt-4o", description="OpenAI model identifier to use for this agent")
    description: str = Field(default="", description="Description of the agent")
    instructions: str | Callable[..., str] = Field(
        default="You are a helpful agent.",
        description="Static string or callable returning agent instructions",
    )
    functions: list[AgentFunction] = Field(default_factory=list, description="List of functions available to the agent")
    tool_choice: Literal["none", "auto", "required"] = Field(
        default="required",
        description="Specific tool selection strategy. none = no tools get called, auto = llm decides if generating a text or calling a tool, required = tools are forced",
    )
    parallel_tool_calls: bool = Field(default=False, description="Whether multiple tools can be called in parallel")
    provider_config: LiteLLMConfig = Field(default=LiteLLMConfig(), description="Provider Config")
    budget: BudgetService = Field(default=BudgetService(), description="Budget Config")
    # force_tool_use: bool = Field(default=False, description="Force tool use")


class Response(BaseModel):
    """Encapsulates the complete response from an agent interaction.

    Attributes:
        messages: List of message exchanges during the interaction
        agent: The final agent state after the interaction
        context_variables: Updated context variables after the interaction
    """

    messages: list[Message] = Field(
        default_factory=list,
        description="List of messages exchanged during the interaction",
    )
    agent: Agent | None = Field(default=None, description="Final agent state after interaction")
    context_variables: dict[str, Any] = Field(
        default_factory=dict, description="Updated context variables after interaction"
    )


class Result(BaseModel):
    """Encapsulates the return value from an agent function execution.

    Attributes:
        value: The string result of the function execution
        agent: Optional new agent to switch to after this result
        context_variables: Updated context variables from this execution
    """

    value: str = Field(default="", description="String result of the function execution")
    agent: Agent | None = Field(default=None, description="Optional new agent to switch to")
    context_variables: dict[str, Any] = Field(
        default_factory=dict,
        description="Updated context variables from this execution",
    )

    class Config:
        """Pydantic configuration for better error messages."""

        error_msg_templates: ClassVar[dict[str, str]] = {
            "type_error": "Invalid type for {field_name}: {error_msg}",
            "value_error": "Invalid value for {field_name}: {error_msg}",
        }
