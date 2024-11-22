"""Base class for event handle providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from schwarm.events.event_data import Event
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.provider.provider_context import ProviderContext


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for event handle providers."""


@dataclass
class BaseEventHandleProvider(BaseProvider, ABC):
    """Base class for event handle providers."""

    event_log: list[Event] = field(default_factory=list)

    # def __init__(self, *args, **kwargs):
    #     """Initializes the provider."""
    #     raise RuntimeError("Use ProviderManager to create provider instances")

    @abstractmethod
    def handle_event(self, event: Event) -> ProviderContext:
        """Handle an event."""
        self.event_log.append(event)
