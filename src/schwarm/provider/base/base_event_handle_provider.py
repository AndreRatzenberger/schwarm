"""Base class for event-based providers."""

from abc import ABC
from collections.abc import Callable
from typing import Any

from schwarm.events.event_types import EventType
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig


class BaseEventHandleProvider(BaseProvider, ABC):
    """Base class for providers that handle internal events.

    Event-based providers can be used both externally (in tools) and internally
    (responding to system events). They must define which events they handle
    and provide appropriate handlers.
    """

    def __init__(self, config: BaseProviderConfig):
        """Initialize the provider."""
        super().__init__(config)
        self.external_use: bool = False
        self.internal_use: dict[EventType, list[Callable]] = {}

    def set_up(self) -> None:
        """Set up event handlers and external use flag.

        Subclasses should override this to configure:
        - self.external_use: Whether the provider can be used in tools
        - self.internal_use: Map of events to handler functions
        """
        pass

    def handle_event(self, event_type: EventType, *args, **kwargs) -> Any:
        """Handle an internal event.

        Args:
            event_type: The type of event to handle
            args: Positional arguments for the handler
            kwargs: Keyword arguments for the handler

        Returns:
            Any result from the event handlers
        """
        if event_type in self.internal_use:
            for handler in self.internal_use[event_type]:
                result = handler(*args, **kwargs)
                if result is not None:
                    return result
        return None

    def complete(self, messages: list[str]) -> str:
        """Default implementation for providers that don't need completion.

        Event-based providers may not need completion functionality if they're
        primarily used for internal event handling.
        """
        raise NotImplementedError("This provider does not support completion")
