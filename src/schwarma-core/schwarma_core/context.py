"""Context module for managing shared state between components."""

from typing import Any, TypeVar

from .events import Event, EventDispatcher, EventType

T = TypeVar("T")


class Context:
    """Manages shared state and variables between components.

    The Context class provides a thread-safe way to store and access
    shared data, with event notifications for state changes.

    Example:
        context = Context()
        context.set("user_name", "Alice")
        name = context.get("user_name")  # Returns "Alice"
        context.clear()  # Removes all variables
    """

    def __init__(self, event_dispatcher: EventDispatcher | None = None) -> None:
        """Initialize a new context.

        Args:
            event_dispatcher: Optional event dispatcher for context events
        """
        self._variables: dict[str, Any] = {}
        self._event_dispatcher = event_dispatcher or EventDispatcher()

    def get(self, key: str, default: T | None = None) -> T | None:
        """Get a value from the context.

        Args:
            key: The key to look up
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key, or default if not found
        """
        return self._variables.get(key, default)  # type: ignore

    async def set(self, key: str, value: Any) -> None:
        """Set a value in the context.

        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._variables[key] = value
        await self._dispatch_event(
            EventType.CONTEXT_UPDATED,
            {
                "key": key,
                "value": value,
            },
        )

    async def delete(self, key: str) -> None:
        """Delete a value from the context.

        Args:
            key: The key to remove
        """
        if key in self._variables:
            del self._variables[key]
            await self._dispatch_event(
                EventType.CONTEXT_UPDATED,
                {
                    "key": key,
                    "action": "delete",
                },
            )

    async def clear(self) -> None:
        """Remove all variables from the context."""
        self._variables.clear()
        await self._dispatch_event(
            EventType.CONTEXT_CLEARED,
            {},
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the context to a dictionary.

        Returns:
            Dictionary containing all context variables
        """
        return dict(self._variables)

    async def update(self, variables: dict[str, Any]) -> None:
        """Update multiple variables at once.

        Args:
            variables: Dictionary of variables to update
        """
        self._variables.update(variables)
        await self._dispatch_event(
            EventType.CONTEXT_UPDATED,
            {
                "updated_keys": list(variables.keys()),
                "values": variables,
            },
        )

    async def _dispatch_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Dispatch a context-related event.

        Args:
            event_type: The type of event to dispatch
            data: Event-specific data
        """
        await self._event_dispatcher.dispatch(
            Event(
                type=event_type,
                data=data,
                source="context",
            )
        )

    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the context.

        Args:
            key: The key to check

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._variables

    def __len__(self) -> int:
        """Get the number of variables in the context.

        Returns:
            Number of variables
        """
        return len(self._variables)
