"""Base class for event-based providers."""

from abc import ABC
from collections.abc import Callable

from pydantic import Field

from schwarm.events.event_types import EventType
from schwarm.models.provider_context import ProviderContext
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for a provider.

    Attributes:
        provider_id: The provider id.
    """

    external_use: bool = Field(default=False, description="Whether the provider can be used in tools")
    internal_use: dict[EventType, list[Callable]] = {}


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

    def handle_event(self, event_type: EventType, provider_context: ProviderContext) -> ProviderContext | None:
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
                result = handler(provider_context)
                if result is not None:
                    return result
        return None

    def complete(self, messages: list[str]) -> str:
        """Default implementation for providers that don't need completion.

        Event-based providers may not need completion functionality if they're
        primarily used for internal event handling.
        """
        raise NotImplementedError("This provider does not support completion")
