"""Event system for inter-component communication."""

from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, TypeAlias


class EventType(Enum):
    """Enumeration of all possible event types in the system."""

    # Agent lifecycle events
    AGENT_INITIALIZED = auto()
    AGENT_DESTROYED = auto()

    # Function execution events
    BEFORE_FUNCTION_EXECUTION = auto()
    AFTER_FUNCTION_EXECUTION = auto()
    FUNCTION_ERROR = auto()

    # Provider events
    BEFORE_PROVIDER_EXECUTION = auto()
    AFTER_PROVIDER_EXECUTION = auto()
    PROVIDER_ERROR = auto()

    # Context events
    CONTEXT_UPDATED = auto()
    CONTEXT_CLEARED = auto()


@dataclass
class Event:
    """Event data structure containing type and associated data.

    Attributes:
        type: The type of event
        data: Dictionary containing event-specific data
        source: Identifier of the event source
    """

    type: EventType
    data: dict[str, Any]
    source: str


# Event listeners can be either async or sync functions
EventListener: TypeAlias = Callable[[Event], Coroutine[Any, Any, None]] | Callable[[Event], None]


class EventDispatcher:
    """Manages event distribution to registered listeners.

    The EventDispatcher maintains a registry of event listeners and
    handles the distribution of events to appropriate listeners.

    Example:
        dispatcher = EventDispatcher()
        dispatcher.add_listener(EventType.AGENT_INITIALIZED, log_init)
        await dispatcher.dispatch(Event(EventType.AGENT_INITIALIZED, {...}, "agent1"))
    """

    def __init__(self) -> None:
        """Initialize a new event dispatcher."""
        self._listeners: dict[EventType, list[EventListener]] = {}

    def add_listener(self, event_type: EventType, listener: EventListener) -> None:
        """Register a listener for a specific event type.

        Args:
            event_type: The type of event to listen for
            listener: Callback function to execute when event occurs
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)

    def remove_listener(self, event_type: EventType, listener: EventListener) -> None:
        """Remove a listener for a specific event type.

        Args:
            event_type: The type of event
            listener: The listener to remove
        """
        if event_type in self._listeners:
            self._listeners[event_type].remove(listener)
            if not self._listeners[event_type]:
                del self._listeners[event_type]

    async def dispatch(self, event: Event) -> None:
        """Dispatch an event to all registered listeners.

        Args:
            event: The event to dispatch
        """
        if event.type in self._listeners:
            for listener in self._listeners[event.type]:
                if callable(getattr(listener, "__await__", None)):
                    await listener(event)  # type: ignore
                else:
                    listener(event)  # type: ignore
