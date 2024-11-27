"""Base class for event handle providers."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import Field

from schwarm.events.event import Event
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for event handle providers."""

    config_type: str = Field(default="event_provider", description="Configuration type")


class BaseEventHandleProvider(BaseProvider, ABC):
    """Base class for event handle providers."""

    event_log: list[Event] = []

    @abstractmethod
    def handle_event(self, event: Event) -> dict[str, Any] | None:
        """Handle an event."""
        self.event_log.append(event)
