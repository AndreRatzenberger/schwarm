"""Function module containing the base Function class."""

from collections.abc import Callable
from typing import Any

from ..context.context import Context


class Function:
    """Represents an action that an agent can perform.

    Functions encapsulate discrete pieces of functionality that can be
    executed by agents. They can be synchronous or asynchronous and have
    access to the shared context.

    Example:
        async def greet(context: Context, name: str) -> str:
            return f"Hello, {name}!"

        greet_function = Function(
            name="greet",
            implementation=greet,
            description="Greets a user by name."
        )
    """

    def __init__(
        self,
        name: str,
        implementation: Callable[..., Any],
        description: str | None = None,
    ) -> None:
        """Initialize a new function.

        Args:
            name: The name of the function
            implementation: The callable that implements the function's behavior
            description: Optional description of what the function does
        """
        self.name = name
        self._implementation = implementation
        self.description = description or "No description provided"

    async def execute(self, context: Context, *args: Any, **kwargs: Any) -> Any:
        """Execute the function with the given context and arguments.

        Args:
            context: The shared context object
            *args: Positional arguments to pass to the implementation
            **kwargs: Keyword arguments to pass to the implementation

        Returns:
            The result of executing the function

        Note:
            The implementation can be either synchronous or asynchronous.
            This method will handle both cases appropriately.
        """
        # Pass context as first argument to implementation
        result = self._implementation(context, *args, **kwargs)

        # Handle both async and sync implementations
        if hasattr(result, "__await__"):
            return await result
        return result

    def __str__(self) -> str:
        """Return a string representation of the function.

        Returns:
            A string containing the function's name and description
        """
        return f"Function(name='{self.name}', description='{self.description}')"

    def __repr__(self) -> str:
        """Return a detailed string representation of the function.

        Returns:
            A string containing all relevant function details
        """
        return (
            f"Function(name='{self.name}', "
            f"implementation={self._implementation.__name__}, "
            f"description='{self.description}')"
        )
