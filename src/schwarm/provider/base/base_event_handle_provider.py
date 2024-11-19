"""Base class for event handle providers."""

from collections.abc import Callable
from typing import Any

from loguru import logger

from schwarm.models.types import Agent
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.models.base_event_handle_provider_config import BaseEventHandleProviderConfig


class BaseEventHandleProvider(BaseProvider):
    """Abstract base class for event handle providers."""

    config: BaseEventHandleProviderConfig
    _event_handlers: dict[str, list[tuple[Callable, int]]] = {}  # {event_name: [(handler, priority)]}

    def __init__(self, agent: Agent, config: BaseEventHandleProviderConfig):
        """Initialize the provider with event handling capabilities."""
        super().__init__(agent, config)
        self._event_handlers = {}

    def subscribe(self, event_name: str, handler: Callable, priority: int = 0) -> None:
        """Subscribe to an event with optional priority.

        Args:
            event_name: Name of the event to subscribe to
            handler: Callback function to handle the event
            priority: Priority level (higher numbers execute first)
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append((handler, priority))
        # Sort handlers by priority (descending)
        self._event_handlers[event_name].sort(key=lambda x: x[1], reverse=True)
        logger.debug(f"Subscribed to event {event_name} with priority {priority}")

    def publish(self, event_name: str, **kwargs: Any) -> None:
        """Publish an event to all subscribers.

        Args:
            event_name: Name of the event to publish
            **kwargs: Event data to pass to handlers
        """
        if event_name in self._event_handlers:
            for handler, _ in self._event_handlers[event_name]:
                try:
                    handler(**kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_name}: {e}")

    # Lifecycle Events
    def on_start(self) -> None:
        """Run when an agent is started."""
        self.publish("on_start")

    def on_handoff(self, next_agent: Agent) -> Agent | None:
        """Run when an agent is handing off task to another agent."""
        self.publish("on_handoff", next_agent=next_agent)
        return next_agent

    def on_message_completion(self) -> None:
        """Run when an agent is sending a message."""
        self.publish("on_message_completion")

    def on_tool_execution(self) -> None:
        """Run when an agent is executing a tool."""
        self.publish("on_tool_execution")

    def on_post_message_completion(self) -> None:
        """Run after a message is sent and result is received."""
        self.publish("on_post_message_completion")

    def on_post_tool_execution(self) -> None:
        """Run after a tool is executed and result is received."""
        self.publish("on_post_tool_execution")
