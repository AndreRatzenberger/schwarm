"""Agent model definition."""

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, Field

from schwarm.configs.base.base_config import BaseConfig


class Agent(BaseModel):
    """An agent with specific capabilities through providers."""

    name: str = Field(default="Agent", description="Identifier name for the agent")
    model: str = Field(default="gpt-4", description="OpenAI model identifier to use for this agent")
    description: str = Field(default="", description="Description of the agent")
    instructions: str | Callable[..., str] = Field(
        default="You are a helpful agent.",
        description="Static string or callable returning agent instructions",
    )
    functions: list[Callable[..., Any]] = Field(
        default_factory=list, description="List of functions available to the agent"
    )
    tool_choice: Literal["none", "auto", "required"] = Field(
        default="required",
        description="Specific tool selection strategy. none = no tools get called, auto = llm decides if generating a text or calling a tool, required = tools are forced",
    )
    parallel_tool_calls: bool = Field(default=False, description="Whether multiple tools can be called in parallel")
    configs: list[BaseConfig] = Field(default_factory=list, description="List of configurations")
    provider_names: list[str] = Field(default_factory=list, description="List of provider IDs")
