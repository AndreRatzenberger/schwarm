"""Defines Pydantic models for agent types and interaction results."""

from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel, Field

from schwarm.models.message import Message

if TYPE_CHECKING:
    from schwarm.models.agent import Agent


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
