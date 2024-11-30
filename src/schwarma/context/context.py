"""Context module containing the Context class for managing shared state."""

from typing import Any


class Context:
    """Manages shared state accessible by agents and functions.

    The Context class provides thread-safe access to a shared state dictionary
    that can be used to store and retrieve data across different components
    of the system.

    Example:
        context = Context()
        context.set("user_name", "Alice")
        name = context.get("user_name")  # Returns "Alice"
    """

    def __init__(self) -> None:
        """Initialize an empty context."""
        self._variables: dict[str, Any] = {}

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from the context.

        Args:
            key: The key to look up
            default: Value to return if key doesn't exist

        Returns:
            The value associated with the key, or the default if not found
        """
        return self._variables.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a value in the context.

        Args:
            key: The key to store the value under
            value: The value to store
        """
        self._variables[key] = value

    def remove(self, key: str) -> None:
        """Remove a value from the context.

        Args:
            key: The key to remove

        If the key doesn't exist, this operation is a no-op.
        """
        self._variables.pop(key, None)

    def clear(self) -> None:
        """Remove all values from the context."""
        self._variables.clear()

    def contains(self, key: str) -> bool:
        """Check if a key exists in the context.

        Args:
            key: The key to check for

        Returns:
            True if the key exists, False otherwise
        """
        return key in self._variables

    def get_all(self) -> dict[str, Any]:
        """Get a copy of all variables in the context.

        Returns:
            A dictionary containing all current context variables
        """
        return self._variables.copy()
