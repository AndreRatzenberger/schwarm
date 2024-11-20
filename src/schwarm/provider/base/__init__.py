"""Base provider classes and utilities."""

# Common event data types
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, List

from schwarm.models.message import Message
from schwarm.provider.base.base_event_handle_provider import Event, ModernEventHandleProvider
from schwarm.provider.base.base_llm_provider import BaseLLMProvider
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.decorators import handles_event
from schwarm.provider.base.models.event_types import EventType
from schwarm.provider.base.models.injection import (
    ContextInjection,
    InjectionTarget,
    InjectionTask,
    InstructionInjection,
    MessageInjection,
)

if TYPE_CHECKING:
    from schwarm.models.agent import Agent


@dataclass
class MessageCompletionData:
    """Data available during message completion events."""

    messages: list[Message]
    context_variables: dict[str, Any]


@dataclass
class ToolExecutionData:
    """Data available during tool execution events."""

    tool_name: str
    args: dict[str, Any]
    context_variables: dict[str, Any]


@dataclass
class HandoffData:
    """Data available during handoff events."""

    next_agent: "Agent"
    current_agent: "Agent"
    context_variables: dict[str, Any]


__all__ = [
    "BaseProvider",
    "BaseLLMProvider",
    "ModernEventHandleProvider",
    "Event",
    "EventType",
    "handles_event",
    "InjectionTask",
    "InjectionTarget",
    "InstructionInjection",
    "MessageInjection",
    "ContextInjection",
    "MessageCompletionData",
    "ToolExecutionData",
    "HandoffData",
]
