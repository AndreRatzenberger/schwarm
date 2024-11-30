"""Enhanced event system with fluent API."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Protocol
import uuid

EventHandler = Callable[['Event'], None]
EventMiddleware = Callable[['Event'], 'Event']


class EventType(Enum):
    """Enumeration of possible event types."""
    
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
    
    # Memory events
    MEMORY_STORED = auto()
    MEMORY_RETRIEVED = auto()
    MEMORY_CLEARED = auto()
    
    # Tool events
    BEFORE_TOOL_EXECUTION = auto()
    AFTER_TOOL_EXECUTION = auto()
    TOOL_ERROR = auto()
    
    # Context events
    CONTEXT_VARIABLE_SET = auto()
    CONTEXT_VARIABLE_REMOVED = auto()
    CONTEXT_CLEARED = auto()


@dataclass
class EventContext:
    """Context for event tracking."""
    trace_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Event:
    """Represents an event in the system."""
    type: EventType
    data: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    context: Optional[EventContext] = None


class EventBuilder:
    """Fluent builder for events.
    
    Example:
        event = (EventBuilder(EventType.TOOL_ERROR)
            .with_data({"error": str(error)})
            .from_source("tool_executor")
            .with_metadata({"severity": "high"})
            .build())
    """
    
    def __init__(self, event_type: EventType):
        """Initialize event builder.
        
        Args:
            event_type: Type of event to build
        """
        self._type = event_type
        self._data: Dict[str, Any] = {}
        self._source: Optional[str] = None
        self._metadata: Dict[str, Any] = {}
        
    def with_data(self, data: Dict[str, Any]) -> 'EventBuilder':
        """Add event data.
        
        Args:
            data: Event data
            
        Returns:
            Self for chaining
        """
        self._data.update(data)
        return self
        
    def from_source(self, source: str) -> 'EventBuilder':
        """Set event source.
        
        Args:
            source: Event source
            
        Returns:
            Self for chaining
        """
        self._source = source
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'EventBuilder':
        """Add event metadata.
        
        Args:
            metadata: Event metadata
            
        Returns:
            Self for chaining
        """
        self._metadata.update(metadata)
        return self
        
    def build(self) -> Event:
        """Build the event.
        
        Returns:
            Configured event
        """
        return Event(
            type=self._type,
            data=self._data or None,
            source=self._source,
            context=EventContext(
                trace_id=str(uuid.uuid4()),
                metadata=self._metadata
            )
        )


class EventDispatcher:
    """Enhanced event dispatcher with middleware support.
    
    Example:
        dispatcher = EventDispatcher()
        
        # Add middleware
        dispatcher.add_middleware(logging_middleware)
        
        # Subscribe to events
        dispatcher.on(EventType.TOOL_ERROR).do(handle_error)
        
        # Dispatch event
        await dispatcher.dispatch(error_event)
    """
    
    def __init__(self):
        """Initialize event dispatcher."""
        self._listeners: Dict[EventType, List[EventHandler]] = {}
        self._middleware: List[EventMiddleware] = []
        self._lock = asyncio.Lock()
        
    def on(self, event_type: EventType) -> 'EventSubscriber':
        """Create subscription for event type.
        
        Args:
            event_type: Type of event to subscribe to
            
        Returns:
            Subscription builder
        """
        return EventSubscriber(self, event_type)
        
    def add_middleware(self, middleware: EventMiddleware) -> None:
        """Add event middleware.
        
        Args:
            middleware: Middleware function
        """
        self._middleware.append(middleware)
        
    async def dispatch(self, event: Event) -> None:
        """Dispatch an event.
        
        Args:
            event: Event to dispatch
        """
        # Apply middleware
        processed_event = await self._apply_middleware(event)
        
        # Notify listeners
        await self._notify_listeners(processed_event)
        
    async def _apply_middleware(self, event: Event) -> Event:
        """Apply middleware chain to event.
        
        Args:
            event: Original event
            
        Returns:
            Processed event
        """
        current_event = event
        for middleware in self._middleware:
            try:
                current_event = await middleware(current_event)
            except Exception as e:
                # Log middleware error but continue chain
                print(f"Middleware error: {e}")
        return current_event
        
    async def _notify_listeners(self, event: Event) -> None:
        """Notify all listeners of an event.
        
        Args:
            event: Event to notify about
        """
        if event.type in self._listeners:
            async with self._lock:
                for listener in self._listeners[event.type]:
                    try:
                        await listener(event)
                    except Exception as e:
                        # Log listener error but continue notifications
                        print(f"Listener error: {e}")
                        
    def _add_listener(
        self,
        event_type: EventType,
        handler: EventHandler
    ) -> None:
        """Add event listener.
        
        Args:
            event_type: Type of event to listen for
            handler: Event handler
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(handler)


class EventSubscriber:
    """Fluent interface for event subscription.
    
    Example:
        dispatcher.on(EventType.TOOL_ERROR)
            .with_filter(lambda e: e.data["severity"] == "high")
            .do(handle_error)
    """
    
    def __init__(
        self,
        dispatcher: EventDispatcher,
        event_type: EventType
    ):
        """Initialize subscriber.
        
        Args:
            dispatcher: Event dispatcher
            event_type: Type of event to subscribe to
        """
        self._dispatcher = dispatcher
        self._event_type = event_type
        self._filter: Optional[Callable[[Event], bool]] = None
        
    def with_filter(
        self,
        filter_func: Callable[[Event], bool]
    ) -> 'EventSubscriber':
        """Add event filter.
        
        Args:
            filter_func: Filter function
            
        Returns:
            Self for chaining
        """
        self._filter = filter_func
        return self
        
    def do(self, handler: EventHandler) -> None:
        """Register event handler.
        
        Args:
            handler: Event handler
        """
        if self._filter:
            # Wrap handler with filter
            async def filtered_handler(event: Event) -> None:
                if self._filter(event):
                    await handler(event)
            self._dispatcher._add_listener(
                self._event_type,
                filtered_handler
            )
        else:
            self._dispatcher._add_listener(
                self._event_type,
                handler
            )
