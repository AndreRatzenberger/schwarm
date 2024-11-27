"""Base models for events."""

from datetime import datetime
from enum import Enum
from typing import Any, TypeVar

from pydantic import BaseModel, Field

from schwarm.models.provider_context import ProviderContextModel

T = TypeVar("T")


class EventType(Enum):
    """Core system events."""

    START_TURN = "on_start_turn"  # agent starts a new turn
    INSTRUCT = "on_instruct"  # agent gets instructed (before instruction gets generated)
    MESSAGE_COMPLETION = "on_message_completion"  # LLM chat completion (before message gets send)
    POST_MESSAGE_COMPLETION = "on_post_message_completion"  # tool execution (after tool gets executed)
    TOOL_EXECUTION = "on_tool_execution"  # tool execution (before tool gets executed)
    POST_TOOL_EXECUTION = "on_post_tool_execution"  # tool execution (after tool gets executed)
    HANDOFF = "on_handoff"  # agent handoff (agent gets changed)
    NONE = "on_begin"


# Base models for specific context pieces
class MessageContext(BaseModel):
    """Context specific to message handling."""

    current_message: Any | None = None
    message_history: list[Any] = Field(default_factory=list)
    current_turn: int
    max_turns: int


class AgentContext(BaseModel):
    """Context specific to agent operations."""

    current_agent: Any
    available_agents: list[Any] = Field(default_factory=list)
    override_model: str | None = None


class ToolContext(BaseModel):
    """Context specific to tool operations."""

    available_tools: list[Any] = Field(default_factory=list)
    context_variables: dict[str, Any] = Field(default_factory=dict)


class PostToolContext(BaseModel):
    """Context specific to tool operations."""

    available_tools: list[Any] = Field(default_factory=list)
    context_variables: dict[str, Any] = Field(default_factory=dict)


class InstructionContext(BaseModel):
    """Context specific to instruction handling."""

    instruction_str: str | None = None
    instruction_func: Any | None = None
    context_variables: dict[str, Any] = Field(default_factory=dict)


# Event-specific context models
class StartEventContext(BaseModel):
    """Context needed for start events."""

    current_agent: Any
    available_agents: list[Any] = Field(default_factory=list)
    available_tools: list[Any] = Field(default_factory=list)
    available_providers: list[Any] = Field(default_factory=dict)
    override_model: str | None = None


class StartTurnContext(MessageContext):
    """Context needed for turn start events."""

    context_variables: dict[str, Any] = Field(default_factory=dict)
    current_agent: Any


class InstructEventContext(InstructionContext):
    """Context needed for instruction events."""

    current_agent: Any


class MessageCompletionContext(MessageContext):
    """Context needed for message completion events."""

    instruction_str: str | None = None
    override_model: str | None = None


class ToolExecutionContext(ToolContext):
    """Context needed for tool execution events."""

    current_agent: Any
    current_message: Any | None = None


class HandoffContext(AgentContext, MessageContext):
    """Context needed for agent handoff events."""

    available_providers: list[Any] = Field(default_factory=dict)


class SpanEvent(BaseModel):
    """Base event model with filtered context."""

    event_type: EventType
    agent: Any
    agent_name: str
    previous_agent: Any | None
    instruction: str | None
    message: Any
    tools: Any
    tool_result: Any
    token_spent: int
    token_cost: float
    current_turn: int
    max_turns: int
    context_variables: dict[str, Any] = Field(default_factory=dict)


# Context filter for converting full context to event-specific context
class ContextFilter:
    """Filters full context into event-specific contexts."""

    @staticmethod
    def for_span_event(full_context: ProviderContextModel, eventType: EventType) -> SpanEvent:
        """Filter context for start events."""
        return SpanEvent(
            event_type=eventType,
            agent=full_context.current_agent,
            agent_name=full_context.current_agent.name if full_context.current_agent else "",
            previous_agent=full_context.previous_agent,
            instruction=full_context.instruction_str,
            message=full_context.current_message,
            tools=full_context.current_tools,
            tool_result=full_context.current_tool_result,
            token_spent=full_context.token_spent,
            token_cost=full_context.token_cost,
            context_variables=full_context.context_variables,
            current_turn=full_context.current_turn,
            max_turns=full_context.max_turns,
        )

    @staticmethod
    def for_start_event(full_context: ProviderContextModel) -> StartEventContext:
        """Filter context for start events."""
        return StartEventContext(
            current_agent=full_context.current_agent,
            available_agents=full_context.available_agents,
            available_tools=full_context.available_tools,
            available_providers=full_context.available_providers,
            override_model=full_context.override_model,
        )

    @staticmethod
    def for_start_turn(full_context: ProviderContextModel) -> StartTurnContext:
        """Filter context for turn start events."""
        return StartTurnContext(
            message_history=full_context.message_history,
            current_turn=full_context.current_turn,
            max_turns=full_context.max_turns,
            context_variables=full_context.context_variables,
            current_agent=full_context.current_agent,
        )

    @staticmethod
    def for_instruct(full_context: ProviderContextModel) -> InstructEventContext:
        """Filter context for instruction events."""
        return InstructEventContext(
            instruction_str=full_context.instruction_str,
            instruction_func=full_context.instruction_func,
            context_variables=full_context.context_variables,
            current_agent=full_context.current_agent,
        )

    @staticmethod
    def for_message_completion(full_context: ProviderContextModel) -> MessageCompletionContext:
        """Filter context for message completion events."""
        return MessageCompletionContext(
            instruction_str=full_context.instruction_str,
            current_message=full_context.current_message,
            current_turn=full_context.current_turn,
            max_turns=full_context.max_turns,
            override_model=full_context.override_model,
        )

    @staticmethod
    def for_tool_execution(full_context: "ProviderContextModel") -> ToolExecutionContext:
        """Filter context for tool execution events."""
        return ToolExecutionContext(
            available_tools=full_context.available_tools,
            context_variables=full_context.context_variables,
            current_agent=full_context.current_agent,
            current_message=full_context.current_message,
        )

    @staticmethod
    def for_post_tool_execution(full_context: "ProviderContextModel") -> ToolExecutionContext:
        """Filter context for tool execution events."""
        return ToolExecutionContext(
            available_tools=full_context.available_tools,
            context_variables=full_context.context_variables,
            current_agent=full_context.current_agent,
            current_message=full_context.current_message,
        )


# Example usage with events
class Event(BaseModel):
    """Base event model with filtered context."""

    type: EventType = Field(default=EventType.NONE, description="Event type")
    agent_name: str = Field(default="", description="Name of the agent")
    provider_id: str = Field(default="", description="Name of the provider")
    timestamp: str = Field(default=datetime.now(), description="Event timestamp")
    context: Any = Field(default=None, description="Event context")


def create_start_event(context: "ProviderContextModel") -> Event:
    """Create start event with filtered context."""
    filtered_context = ContextFilter.for_start_event(context)
    return Event(
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=filtered_context,
    )


def create_start_turn_event(context: "ProviderContextModel") -> Event:
    """Create turn start event with filtered context."""
    filtered_context = ContextFilter.for_start_turn(context)
    return Event(
        type=EventType.START_TURN,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=filtered_context,
    )


def create_instruct_event(context: "ProviderContextModel", instruction: str | None = None) -> Event:
    """Create instruction event with filtered context."""
    filtered_context = ContextFilter.for_instruct(context)
    if instruction:
        filtered_context.instruction_str = instruction

    return Event(
        type=EventType.INSTRUCT,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=filtered_context,
    )


def create_message_completion_event(context: "ProviderContextModel") -> Event:
    """Create message completion event with filtered context."""
    filtered_context = ContextFilter.for_message_completion(context)
    return Event(
        type=EventType.MESSAGE_COMPLETION,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=filtered_context,
    )


def create_tool_execution_event(
    context: "ProviderContextModel",
) -> Event:
    """Create tool execution event with filtered context."""
    filtered_context = ContextFilter.for_tool_execution(context)
    return Event(
        type=EventType.TOOL_EXECUTION,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=filtered_context,
    )


def create_handoff_event(context: "ProviderContextModel") -> Event:
    """Create handoff event with filtered context."""
    return Event(
        type=EventType.HANDOFF,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context="",
    )


def create_full_event(context: "ProviderContextModel", event_type: EventType) -> Event | None:
    """Create full event with full context."""
    return Event(
        type=event_type,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=context,
    )


def create_post_message_completion_event(context: "ProviderContextModel") -> Event | None:
    """Create full event with full context."""
    return Event(
        type=EventType.POST_MESSAGE_COMPLETION,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=context,
    )


def create_post_tool_execution_event(context: "ProviderContextModel") -> Event:
    """Create full event with full context."""
    return Event(
        type=EventType.POST_TOOL_EXECUTION,
        agent_name=context.current_agent.name if context.current_agent else "",
        timestamp=datetime.utcnow().isoformat(),
        context=context,
    )


def create_event(context: "ProviderContextModel", event_type: EventType) -> SpanEvent | None:
    """Event switch."""
    return ContextFilter.for_span_event(context, eventType=event_type)
