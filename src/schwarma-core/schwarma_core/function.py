"""Function interface defining the contract for executable capabilities."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any, TypeVar

from .events import Event, EventDispatcher, EventType

T = TypeVar("T")


class Function(ABC):
    """Abstract base class for functions that can be executed by agents.

    Functions represent discrete capabilities that can be exposed to agents.
    Each function must implement the execute method and provide metadata
    about its parameters and behavior.

    Example:
        class GreetFunction(Function):
            def __init__(self):
                super().__init__(
                    name="greet",
                    description="Greet someone by name",
                    parameters={
                        "name": {
                            "type": "string",
                            "description": "Name of person to greet"
                        }
                    }
                )

            async def execute(self, name: str) -> str:
                return f"Hello, {name}!"
    """

    def __init__(
        self,
        name: str,
        description: str,
        parameters: dict[str, dict[str, Any]],
        event_dispatcher: EventDispatcher | None = None,
    ) -> None:
        """Initialize a new function.

        Args:
            name: The name of the function
            description: Description of what the function does
            parameters: Dictionary describing function parameters
            event_dispatcher: Optional event dispatcher for function events
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self._event_dispatcher = event_dispatcher or EventDispatcher()

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the function with the provided arguments.

        This method must be implemented by concrete function classes.

        Args:
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            The result of the function execution
        """
        pass

    async def _dispatch_event(self, event_type: EventType, data: dict[str, Any]) -> None:
        """Dispatch a function-related event.

        Args:
            event_type: The type of event to dispatch
            data: Event-specific data
        """
        await self._event_dispatcher.dispatch(
            Event(
                type=event_type,
                data={"function_name": self.name, **data},
                source=self.name,
            )
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert the function to a dictionary representation.

        Returns:
            Dictionary containing function metadata
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


def create_function(
    name: str,
    description: str,
    implementation: Callable[..., T],
    parameters: dict[str, dict[str, Any]],
    event_dispatcher: EventDispatcher | None = None,
) -> Function:
    """Create a new function from a callable.

    This is a convenience function for creating Function instances
    from regular Python functions or methods.

    Args:
        name: The name of the function
        description: Description of what the function does
        implementation: The callable that implements the function
        parameters: Dictionary describing function parameters
        event_dispatcher: Optional event dispatcher for function events

    Returns:
        A new Function instance wrapping the implementation

    Example:
        def greet(name: str) -> str:
            return f"Hello, {name}!"

        greet_function = create_function(
            name="greet",
            description="Greet someone by name",
            implementation=greet,
            parameters={
                "name": {
                    "type": "string",
                    "description": "Name of person to greet"
                }
            }
        )
    """

    class WrappedFunction(Function):
        async def execute(self, *args: Any, **kwargs: Any) -> Any:
            try:
                await self._dispatch_event(
                    EventType.BEFORE_FUNCTION_EXECUTION,
                    {"args": args, "kwargs": kwargs},
                )

                result = (
                    await implementation(*args, **kwargs)
                    if callable(getattr(implementation, "__await__", None))
                    else implementation(*args, **kwargs)
                )  # type: ignore

                await self._dispatch_event(
                    EventType.AFTER_FUNCTION_EXECUTION,
                    {"result": result},
                )

                return result

            except Exception as e:
                await self._dispatch_event(
                    EventType.FUNCTION_ERROR,
                    {"error": str(e)},
                )
                raise

    return WrappedFunction(
        name=name,
        description=description,
        parameters=parameters,
        event_dispatcher=event_dispatcher,
    )
