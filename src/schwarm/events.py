"""Events module containing the event system implementation."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional

class EventType(Enum):
    """Enumeration of possible event types in the system."""
    
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
    CONTEXT_VARIABLE_SET = auto()
    CONTEXT_VARIABLE_REMOVED = auto()
    CONTEXT_CLEARED = auto()


@dataclass
class Event:
    """Represents an event in the system.
    
    Attributes:
        type: The type of the event
        data: Optional data associated with the event
        source: Optional source that triggered the event
    """
    
    type: EventType
    data: Optional[Dict[str, Any]] = None
    source: Optional[str] = None


EventListener = Callable[[Event], None]


class EventDispatcher:
    """Manages event dispatching and listener registration.
    
    The EventDispatcher allows components to register listeners for specific
    event types and handles the dispatching of events to appropriate listeners.
    
    Example:
        dispatcher = EventDispatcher()
        
        async def log_function_execution(event: Event):
            print(f"Function executed: {event.data}")
            
        dispatcher.add_listener(
            EventType.AFTER_FUNCTION_EXECUTION,
            log_function_execution
        )
    """
    
    def __init__(self) -> None:
        """Initialize an empty event dispatcher."""
        self._listeners: Dict[EventType, List[EventListener]] = {}
        
    def add_listener(self, event_type: EventType, listener: EventListener) -> None:
        """Add a listener for a specific event type.
        
        Args:
            event_type: The type of event to listen for
            listener: The callback function to execute when the event occurs
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(listener)
        
    def remove_listener(self, event_type: EventType, listener: EventListener) -> None:
        """Remove a listener for a specific event type.
        
        Args:
            event_type: The type of event the listener was registered for
            listener: The callback function to remove
            
        If the listener wasn't registered, this operation is a no-op.
        """
        if event_type in self._listeners:
            self._listeners[event_type] = [
                l for l in self._listeners[event_type] if l != listener
            ]
            
    async def dispatch(self, event: Event) -> None:
        """Dispatch an event to all registered listeners.
        
        Args:
            event: The event to dispatch
        """
        if event.type in self._listeners:
            for listener in self._listeners[event.type]:
                try:
                    await listener(event)
                except Exception:
                    # Swallow exceptions from listeners to prevent them from affecting other listeners
                    pass
                
    def clear_listeners(self, event_type: Optional[EventType] = None) -> None:
        """Clear listeners for a specific event type or all listeners.
        
        Args:
            event_type: The event type to clear listeners for.
                       If None, clears all listeners.
        """
        if event_type is None:
            self._listeners.clear()
        elif event_type in self._listeners:
            del self._listeners[event_type]
