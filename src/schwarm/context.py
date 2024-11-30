"""Enhanced context management with fluent API."""

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, TypeVar

from .events import Event, EventBuilder, EventDispatcher, EventType

T = TypeVar('T')


@dataclass
class ContextVariable:
    """Represents a variable in context."""
    key: str
    value: Any
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ContextManager:
    """Manages context state with event dispatching.
    
    Example:
        context = ContextManager()
        
        # Set variables
        await context.set("user_id", "123")
            .with_metadata({"source": "auth"})
            .execute()
            
        # Get variables
        user_id = await context.get("user_id")
            .with_default("anonymous")
            .execute()
    """
    
    def __init__(self, event_dispatcher: Optional[EventDispatcher] = None):
        """Initialize context manager.
        
        Args:
            event_dispatcher: Optional event dispatcher
        """
        self._variables: Dict[str, ContextVariable] = {}
        self._event_dispatcher = event_dispatcher or EventDispatcher()
        self._pending_key: Optional[str] = None
        self._pending_value: Any = None
        self._pending_metadata: Dict[str, Any] = {}
        
    def set(self, key: str, value: Any) -> 'ContextManager':
        """Start setting a context variable.
        
        Args:
            key: Variable key
            value: Variable value
            
        Returns:
            Self for chaining
        """
        self._pending_key = key
        self._pending_value = value
        self._pending_metadata = {}
        return self
        
    def with_metadata(self, metadata: Dict[str, Any]) -> 'ContextManager':
        """Add metadata to pending variable.
        
        Args:
            metadata: Variable metadata
            
        Returns:
            Self for chaining
        """
        self._pending_metadata.update(metadata)
        return self
        
    async def execute_set(self) -> None:
        """Execute pending variable set.
        
        Raises:
            ValueError: If no pending set operation
        """
        if self._pending_key is None:
            raise ValueError("No pending set operation")
            
        try:
            now = datetime.utcnow()
            
            if self._pending_key in self._variables:
                # Update existing
                var = self._variables[self._pending_key]
                var.value = self._pending_value
                var.updated_at = now
                var.metadata.update(self._pending_metadata)
            else:
                # Create new
                var = ContextVariable(
                    key=self._pending_key,
                    value=self._pending_value,
                    metadata=self._pending_metadata
                )
                self._variables[self._pending_key] = var
                
            # Dispatch event
            await self._dispatch_event(
                EventType.CONTEXT_VARIABLE_SET,
                {
                    "key": var.key,
                    "value": var.value,
                    "metadata": var.metadata
                }
            )
            
        finally:
            self._pending_key = None
            self._pending_value = None
            self._pending_metadata = {}
            
    def get(self, key: str) -> 'ContextGetter':
        """Start getting a context variable.
        
        Args:
            key: Variable key
            
        Returns:
            Getter for chaining
        """
        return ContextGetter(self, key)
        
    def remove(self, key: str) -> 'ContextManager':
        """Remove a context variable.
        
        Args:
            key: Variable key
            
        Returns:
            Self for chaining
        """
        if key in self._variables:
            var = self._variables.pop(key)
            
            # Dispatch event
            asyncio.create_task(
                self._dispatch_event(
                    EventType.CONTEXT_VARIABLE_REMOVED,
                    {
                        "key": var.key,
                        "value": var.value,
                        "metadata": var.metadata
                    }
                )
            )
            
        return self
        
    async def clear(self) -> None:
        """Clear all context variables."""
        self._variables.clear()
        
        # Dispatch event
        await self._dispatch_event(
            EventType.CONTEXT_CLEARED,
            {}
        )
        
    def get_all(self) -> Dict[str, Any]:
        """Get all context variables.
        
        Returns:
            Dictionary of all variables
        """
        return {
            key: var.value
            for key, var in self._variables.items()
        }
        
    def get_metadata(self, key: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a variable.
        
        Args:
            key: Variable key
            
        Returns:
            Variable metadata if found, None otherwise
        """
        if key in self._variables:
            return self._variables[key].metadata.copy()
        return None
        
    async def _dispatch_event(
        self,
        event_type: EventType,
        data: Dict[str, Any]
    ) -> None:
        """Dispatch a context event.
        
        Args:
            event_type: Type of event
            data: Event data
        """
        if self._event_dispatcher:
            event = (EventBuilder(event_type)
                .with_data(data)
                .from_source("context")
                .build())
            await self._event_dispatcher.dispatch(event)


class ContextGetter:
    """Fluent interface for getting context variables.
    
    Example:
        value = await context.get("key")
            .with_default("fallback")
            .with_type(int)
            .execute()
    """
    
    def __init__(self, manager: ContextManager, key: str):
        """Initialize getter.
        
        Args:
            manager: Context manager
            key: Variable key
        """
        self._manager = manager
        self._key = key
        self._default: Any = None
        self._type: Optional[type] = None
        
    def with_default(self, value: Any) -> 'ContextGetter':
        """Set default value.
        
        Args:
            value: Default value
            
        Returns:
            Self for chaining
        """
        self._default = value
        return self
        
    def with_type(self, type_: type[T]) -> 'ContextGetter':
        """Set expected type.
        
        Args:
            type_: Expected variable type
            
        Returns:
            Self for chaining
        """
        self._type = type_
        return self
        
    def execute(self) -> Any:
        """Execute the get operation.
        
        Returns:
            Variable value or default
            
        Raises:
            TypeError: If value doesn't match expected type
        """
        if self._key in self._manager._variables:
            value = self._manager._variables[self._key].value
        else:
            value = self._default
            
        if value is not None and self._type:
            if not isinstance(value, self._type):
                raise TypeError(
                    f"Expected type {self._type.__name__}, "
                    f"got {type(value).__name__}"
                )
                
        return value
