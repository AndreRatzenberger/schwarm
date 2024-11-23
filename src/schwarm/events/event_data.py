"""Data classes for event payloads and injections."""

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Generic, TypeVar

from pydantic import BaseModel, Field

from schwarm.provider.provider_context import ProviderContext

if TYPE_CHECKING:
    pass

T = TypeVar("T")


@dataclass
class OnChangePayload(Generic[T]):
    """Payload for on_change events."""

    name: str
    old_value: T
    new_value: T


class EventType(Enum):
    """Core system events."""

    START = "on_start"
    HANDOFF = "on_handoff"
    MESSAGE_COMPLETION = "on_message_completion"
    POST_MESSAGE_COMPLETION = "on_post_message_completion"
    TOOL_EXECUTION = "on_tool_execution"
    POST_TOOL_EXECUTION = "on_post_tool_execution"
    INSTRUCT = "on_instruct"
    POST_INSTRUCT = "on_post_instruct"
    NONE = "on_begin"


class Event(BaseModel):
    """Type-safe event with payload."""

    type: EventType = Field(default=EventType.NONE)
    payload: ProviderContext = Field(default_factory=ProviderContext)
    agent_id: str = Field(default="")
    datetime: str = Field(default="")
