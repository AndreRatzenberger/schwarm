# Schwarm Framework Event System Architecture

## Overview

This document focuses on the event and context management system of the Schwarm framework, proposing enhancements while maintaining its powerful flexibility.

## 1. Event Core Architecture

### 1.1 Event Types

```python
# domain/event/types.py
from enum import Enum, auto

class EventType(Enum):
    """Core system events with clear lifecycle stages."""
    
    # Lifecycle Events
    INITIALIZE = auto()
    START = auto()
    SHUTDOWN = auto()
    
    # Agent Events
    AGENT_START = auto()
    AGENT_INSTRUCT = auto()
    AGENT_COMPLETE = auto()
    AGENT_HANDOFF = auto()
    
    # Message Events
    MESSAGE_START = auto()
    MESSAGE_COMPLETE = auto()
    MESSAGE_PROCESS = auto()
    
    # Tool Events
    TOOL_START = auto()
    TOOL_EXECUTE = auto()
    TOOL_COMPLETE = auto()
    
    # Error Events
    ERROR = auto()
    WARNING = auto()

    def is_lifecycle_event(self) -> bool:
        return self in {self.INITIALIZE, self.START, self.SHUTDOWN}

    def is_agent_event(self) -> bool:
        return self in {self.AGENT_START, self.AGENT_INSTRUCT, 
                       self.AGENT_COMPLETE, self.AGENT_HANDOFF}
```

### 1.2 Event Context Models

```python
# domain/event/context.py
from dataclasses import dataclass, field
from typing import Any, Optional
from datetime import datetime

@dataclass(frozen=True)
class BaseContext:
    """Base context for all events."""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class AgentContext(BaseContext):
    """Context for agent-related events."""
    agent_id: str
    agent_name: str
    agent_type: str
    agent_config: dict[str, Any]
    previous_agent_id: Optional[str] = None

@dataclass(frozen=True)
class MessageContext(BaseContext):
    """Context for message-related events."""
    message_id: str
    content: str
    role: str
    metadata: dict[str, Any] = field(default_factory=dict)
    parent_message_id: Optional[str] = None

@dataclass(frozen=True)
class ToolContext(BaseContext):
    """Context for tool-related events."""
    tool_name: str
    tool_args: dict[str, Any]
    tool_result: Optional[Any] = None
    error: Optional[Exception] = None
```

### 1.3 Event Class

```python
# domain/event/event.py
@dataclass(frozen=True)
class Event:
    """Immutable event class."""
    
    type: EventType
    context: BaseContext
    source: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        """Validate event after initialization."""
        self._validate_context()
    
    def _validate_context(self):
        """Ensure context matches event type."""
        expected_context = EVENT_CONTEXT_MAPPING.get(self.type)
        if expected_context and not isinstance(self.context, expected_context):
            raise ValueError(f"Invalid context type for event {self.type}")
```

## 2. Event Bus Implementation

### 2.1 Event Bus

```python
# application/event/bus.py
class EventBus:
    """Central event management system."""
    
    def __init__(self):
        self._subscribers: dict[EventType, list[EventHandler]] = defaultdict(list)
        self._middleware: list[EventMiddleware] = []
        self._lock = asyncio.Lock()

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers."""
        async with self._lock:
            event = await self._apply_middleware(event)
            await self._notify_subscribers(event)

    async def subscribe(
        self,
        event_type: EventType,
        handler: EventHandler,
        priority: int = 0
    ) -> None:
        """Subscribe to events with priority."""
        async with self._lock:
            self._subscribers[event_type].append(handler)
            # Sort by priority
            self._subscribers[event_type].sort(key=lambda h: h.priority)

    async def _apply_middleware(self, event: Event) -> Event:
        """Apply middleware chain to event."""
        current_event = event
        for middleware in self._middleware:
            try:
                current_event = await middleware.process(current_event)
            except Exception as e:
                logger.error(f"Middleware error: {e}")
                # Create error event
                error_event = Event(
                    type=EventType.ERROR,
                    context=ErrorContext(
                        error=e,
                        original_event=event
                    ),
                    source="event_bus"
                )
                await self.publish(error_event)
        return current_event
```

### 2.2 Event Handlers

```python
# application/event/handlers.py
class EventHandler(Protocol):
    """Protocol for event handlers."""
    
    @property
    def priority(self) -> int:
        """Handler priority. Higher numbers execute first."""
        ...

    async def handle(self, event: Event) -> None:
        """Handle an event."""
        ...

class LoggingHandler(EventHandler):
    """Handler for logging events."""
    
    priority = 100  # High priority for logging

    async def handle(self, event: Event) -> None:
        """Log event details."""
        logger.info(
            f"Event: {event.type.name}",
            extra={
                "event_id": str(uuid.uuid4()),
                "event_type": event.type.name,
                "source": event.source,
                "timestamp": event.timestamp.isoformat(),
                "context": asdict(event.context)
            }
        )

class MetricsHandler(EventHandler):
    """Handler for collecting metrics."""
    
    priority = 90  # High priority for metrics

    async def handle(self, event: Event) -> None:
        """Record event metrics."""
        metrics.increment_counter(
            f"events_total",
            {"event_type": event.type.name}
        )
```

### 2.3 Event Middleware

```python
# application/event/middleware.py
class EventMiddleware(Protocol):
    """Protocol for event middleware."""
    
    async def process(self, event: Event) -> Event:
        """Process an event."""
        ...

class ValidationMiddleware(EventMiddleware):
    """Middleware for validating events."""
    
    async def process(self, event: Event) -> Event:
        """Validate event structure and content."""
        try:
            self._validate_event(event)
            return event
        except ValidationError as e:
            raise EventProcessingError(f"Validation failed: {e}")

class EnrichmentMiddleware(EventMiddleware):
    """Middleware for enriching events with additional data."""
    
    async def process(self, event: Event) -> Event:
        """Enrich event with additional context."""
        context = self._enrich_context(event.context)
        return replace(event, context=context)
```

## 3. Context Management

### 3.1 Context Manager

```python
# application/context/manager.py
class ContextManager:
    """Manages context throughout event lifecycle."""
    
    def __init__(self):
        self._context_store = ContextStore()
        self._context_validators = []

    async def create_context(
        self,
        context_type: type[BaseContext],
        **kwargs
    ) -> BaseContext:
        """Create and validate new context."""
        context = context_type(**kwargs)
        await self._validate_context(context)
        await self._context_store.store(context)
        return context

    async def get_context(
        self,
        context_id: str
    ) -> Optional[BaseContext]:
        """Retrieve context by ID."""
        return await self._context_store.get(context_id)

    async def update_context(
        self,
        context_id: str,
        updates: dict[str, Any]
    ) -> BaseContext:
        """Update existing context."""
        context = await self._context_store.get(context_id)
        if not context:
            raise ContextNotFoundError(context_id)
        
        updated_context = replace(context, **updates)
        await self._validate_context(updated_context)
        await self._context_store.store(updated_context)
        return updated_context
```

## 4. Implementation Guidelines

### 4.1 Event Design Principles

1. **Immutability**
   - Events should be immutable
   - Use frozen dataclasses
   - Create new events for updates

2. **Context Isolation**
   - Keep contexts focused
   - Use inheritance wisely
   - Validate context types

3. **Error Handling**
   - Create error events
   - Use middleware for validation
   - Implement retry policies

### 4.2 Performance Considerations

1. **Event Processing**
   - Use async handlers
   - Implement priority system
   - Consider batch processing

2. **Context Management**
   - Use efficient storage
   - Implement caching
   - Clean up old contexts

### 4.3 Monitoring

1. **Event Metrics**
   - Track event counts
   - Measure processing time
   - Monitor error rates

2. **Context Metrics**
   - Track context creation
   - Monitor context size
   - Track context updates

## 5. Migration Strategy

### Phase 1: Event System
1. Implement new event types
2. Add event validation
3. Create event bus

### Phase 2: Context System
1. Implement context models
2. Add context validation
3. Create context manager

### Phase 3: Handlers & Middleware
1. Implement core handlers
2. Add middleware chain
3. Add monitoring

## Conclusion

This enhanced event system architecture provides a robust foundation for managing the complex interactions within the Schwarm framework. The immutable event design, combined with strong context management and flexible handling, ensures reliable and maintainable event processing while maintaining the framework's core flexibility.
