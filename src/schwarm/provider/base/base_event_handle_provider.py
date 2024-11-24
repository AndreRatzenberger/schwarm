"""Base class for event handle providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from schwarm.events.event import Event
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for event handle providers."""

    config_type: str = field(default="event_provider", init=False, repr=False, compare=False)


@dataclass
class BaseEventHandleProvider(BaseProvider, ABC):
    """Base class for event handle providers."""

    event_log: list[Event] = field(default_factory=list)

    @abstractmethod
    def handle_event(self, event: Event) -> dict[str, Any] | None:
        """Handle an event."""
        self.event_log.append(event)
