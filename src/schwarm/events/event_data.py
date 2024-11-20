"""Data classes for event payloads and injections."""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Generic, TypeVar

from schwarm.events.event_types import EventType

if TYPE_CHECKING:
    from schwarm.models.message import Message
    from schwarm.models.types import Agent

T = TypeVar("T")


@dataclass
class Event(Generic[T]):
    """Type-safe event with payload."""

    type: EventType
    payload: T
    agent_id: str


# Event-specific data types
@dataclass
class HandoffData:
    """Data for agent handoff events."""

    current_agent: "Agent"
    next_agent: "Agent"
    context_variables: dict[str, Any]


@dataclass
class MessageCompletionData:
    """Data for message completion events."""

    messages: list["Message"]
    context_variables: dict[str, Any]
    model_override: str | None = None


@dataclass
class ToolExecutionData:
    """Data for tool execution events."""

    tool_name: str
    tool_args: dict[str, Any]
    context_variables: dict[str, Any]


@dataclass
class InstructionData:
    """Data for instruction events."""

    agent_name: str
    instructions: str
    variables: dict[str, Any]
