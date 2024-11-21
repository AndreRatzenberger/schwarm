"""Base class for event handle providers."""

from abc import abstractmethod
from collections.abc import Callable

from schwarm.events.event_data import Event
from schwarm.events.event_types import EventType
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.provider.provider_context import ProviderContext


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for event handle providers."""


class BaseEventHandleProvider(BaseProvider):
    """Base class for event handle providers."""

    config: BaseEventHandleProviderConfig
    context: ProviderContext | None = None
    internal_use: dict[EventType, list[tuple[Callable, int] | Callable]] = {}

    def set_context(self, context: ProviderContext) -> None:
        """Set the provider context."""
        self.context = context

    @abstractmethod
    def handle_event(self, event: Event) -> ProviderContext:
        """Handle an event."""
        raise NotImplementedError
