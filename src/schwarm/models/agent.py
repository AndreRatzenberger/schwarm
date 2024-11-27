"""Agent model definition."""

from collections.abc import Callable
from typing import Any, ClassVar, Literal

from pydantic import BaseModel, Field

from schwarm.configs.base.base_config import BaseConfig
from schwarm.utils.handling import deserialize_callable, serialize_callable


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
    token_spent: int = Field(default=0, description="Amount of tokens spent on this agent")
    total_cost: float = Field(default=0.0, description="Total cost of using")
    parallel_tool_calls: bool = Field(default=False, description="Whether multiple tools can be called in parallel")
    configs: list[BaseConfig] = Field(default_factory=list, description="List of configurations")
    provider_names: list[str] = Field(default_factory=list, description="List of provider IDs")

    def to_dict(self):
        return {
            "name": self.name,
            "model": self.model,
            "description": self.description,
            "instructions": serialize_callable(self.instructions),
            "functions": [serialize_callable(f) for f in self.functions],
            "tool_choice": self.tool_choice,
            "parallel_tool_calls": self.parallel_tool_calls,
            "configs": [c.dict() if isinstance(c, BaseModel) else c for c in self.configs],
            "provider_names": self.provider_names,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data["name"],
            model=data["model"],
            description=data["description"],
            instructions=deserialize_callable(data["instructions"]),
            functions=[deserialize_callable(f) for f in data["functions"]],
            tool_choice=data["tool_choice"],
            parallel_tool_calls=data["parallel_tool_calls"],
            configs=data["configs"],  # Assuming configs are simple or deserializable
            provider_names=data["provider_names"],
        )


class Result(BaseModel):
    """Encapsulates the return value from an agent function execution.

    Attributes:
        value: The string result of the function execution
        agent: Optional new agent to switch to after this result
        context_variables: Updated context variables from this execution
    """

    value: str = Field(default="", description="String result of the function execution")
    agent: "Agent | None" = Field(default=None, description="Optional new agent to switch to")
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
