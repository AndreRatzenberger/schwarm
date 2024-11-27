"""Models for the message in the conversation."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Represents a message in the conversation.

    Attributes:
        role: The role of the message sender (user or assistant)
        content: The content of the message
        sender: Optional identifier of the message sender
        name: Optional name/identifier of the model or user
    """

    role: Literal["user", "assistant", "system", "tool"] = Field(..., description="Role of the message sender")
    content: str | None = Field(default="", description="Content of the message")
    sender: str | None = Field(default=None, description="Identifier of the message sender")
    name: str | None = Field(default=None, description="Name/identifier of the model or user")
    tool_calls: list[Any] | None = Field(default_factory=list, description="List of tool calls")
    tool_call_id: str | None = Field(default=None, description="Identifier of the tool call")
    info: "MessageInfo | None" = Field(default=None, description="Information about the message")
    additional_info: dict[str, Any] = Field(
        default_factory=dict, description="Additional information about the message"
    )


class MessageInfo(BaseModel):
    """Represents additional information about a message.

    Attributes:
        token_counter: Token counter for the message
        completion_cost: Cost of generating the completion
    """

    token_counter: int = Field(..., description="Token counter for the message")
    completion_cost: float = Field(..., description="Cost of generating the completion")
