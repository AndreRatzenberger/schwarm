"""Base models for events."""

from dataclasses import dataclass
from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from schwarm.models.provider_context import ProviderContextModel

T = TypeVar("T")


@dataclass
class OnChangePayload(Generic[T]):
    """Payload for on_change events."""

    name: str
    old_value: T
    new_value: T


class EventType(Enum):
    """Core system events."""

    START = "on_start"  # agent gets initialized
    START_TURN = "on_start_turn"  # agent starts a new turn
    INSTRUCT = "on_instruct"  # agent gets instructed (before instruction gets generated)
    POST_INSTRUCT = "on_post_instruct"  # agent gets instructed (after instruction gets generated)
    MESSAGE_COMPLETION = "on_message_completion"  # LLM chat completion (before message gets send)
    POST_MESSAGE_COMPLETION = "on_post_message_completion"  # LLM chat completion (after answer is received)
    TOOL_EXECUTION = "on_tool_execution"  # tool execution (before tool gets executed)
    POST_TOOL_EXECUTION = "on_post_tool_execution"  # tool execution (tool execution completed)
    HANDOFF = "on_handoff"  # agent handoff (agent gets changed)
    NONE = "on_begin"


class Event(BaseModel):
    """Type-safe event with payload."""

    type: EventType = Field(default=EventType.NONE)
    payload: ProviderContextModel = Field(default_factory=ProviderContextModel)
    agent_id: str = Field(default="")
    datetime: str = Field(default="")
