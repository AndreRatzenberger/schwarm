"""Base class for event handle providers."""

from collections.abc import Callable
from typing import Any

from schwarm.events.event_types import EventType
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.provider.provider_context import ProviderContext


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for event handle providers."""

    def __init__(self, **data):
        """Initialize the event handle provider configuration."""
        super().__init__(
            provider_type="event",
            provider_name="base_event_handle",
            scope="scoped",
            **data,
        )


class BaseEventHandleProvider(BaseProvider):
    """Base class for event handle providers."""

    config: BaseEventHandleProviderConfig
    context: ProviderContext | None = None
    internal_use: dict[EventType, list[tuple[Callable, int] | Callable]] = {}

    def set_context(self, context: ProviderContext) -> None:
        """Set the provider context."""
        self.context = context

    def handle_start(self, event: Any = None) -> None:
        """Handle agent start."""
        pass

    def handle_instruct(self, event: Any = None) -> None:
        """Handle agent instructions."""
        pass

    def handle_message_completion(self, event: Any = None) -> None:
        """Handle message completion."""
        pass

    def handle_tool_execution(self, event: Any = None) -> None:
        """Handle tool execution."""
        pass

    def handle_post_tool_execution(self, event: Any = None) -> None:
        """Handle post tool execution."""
        pass

    def handle_handoff(self, event: Any = None) -> None:
        """Handle agent handoff."""
        pass

    def handle_error(self, event: Any = None) -> None:
        """Handle error."""
        pass
