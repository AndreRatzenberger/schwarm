"""Base provider implementation."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from schwarm.events.event_types import EventType
from schwarm.provider.base.base_provider_config import BaseProviderConfig


class BaseProvider(ABC):
    """Base class for all providers."""

    def __init__(self, config: BaseProviderConfig):
        """Initialize the provider."""
        self.config = config
        self.external_use: bool = False
        self.internal_use: dict[EventType, list[Callable]] = {}

    def set_up(self) -> None:
        """Initialize the provider. Override this in subclasses."""
        pass

    def handle_event(self, event_type: EventType, *args, **kwargs) -> Any:
        """Handle internal events if configured."""
        if event_type in self.internal_use:
            for handler in self.internal_use[event_type]:
                result = handler(*args, **kwargs)
                if result is not None:
                    return result
        return None

    @abstractmethod
    def complete(self, messages: list[str]) -> str:
        """Complete a prompt using the provider.

        Args:
            messages: List of messages to process

        Returns:
            Completion response as a string
        """
        pass
