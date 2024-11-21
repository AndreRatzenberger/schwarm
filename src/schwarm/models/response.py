"""Response types for the Schwarm framework."""

from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, Field

from schwarm.models.agent import Agent
from schwarm.models.message import Message
from schwarm.models.result import Result

# Type aliases
ContextVariables = dict[str, Any]
AgentFunction = Callable[..., "str | Agent | dict[str, Any] | Result"]


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
    context_variables: ContextVariables = Field(
        default_factory=dict, description="Updated context variables after interaction"
    )
