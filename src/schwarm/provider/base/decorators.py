"""Event handling decorators for providers."""

from collections.abc import Callable
from functools import wraps
from typing import TypeVar

from typing_extensions import ParamSpec

from schwarm.provider.base.models.injection import InjectionTask

P = ParamSpec("P")
T = TypeVar("T")


def handles_event(event_type: str, priority: int = 0):
    """Decorator to mark methods as event handlers.

    This decorator allows for a more modern and type-safe way to handle events
    in providers. Instead of overriding handle_* methods, providers can use
    this decorator to mark any method as an event handler.

    Example:
        @handles_event(EventType.START)
        def initialize(self, event: Event[dict[str, Any]]) -> None:
            # Handle start event
            pass

    Args:
        event_type: The type of event to handle
        priority: Optional priority for the handler (higher executes first)
    """

    def decorator(func: Callable[P, InjectionTask | None]) -> Callable[P, InjectionTask | None]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> InjectionTask | None:
            return func(*args, **kwargs)

        # Store event handling info on the function
        setattr(wrapper, "_handles_event", True)
        setattr(wrapper, "_event_type", event_type)
        setattr(wrapper, "_priority", priority)

        return wrapper

    return decorator
