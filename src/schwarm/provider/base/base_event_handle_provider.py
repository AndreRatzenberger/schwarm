"""Base class for event handle providers."""

from collections.abc import Callable
from typing import Any, Literal

from loguru import logger
from pydantic import BaseModel, Field

from schwarm.models.agent import Agent
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.models.base_event_handle_provider_config import BaseEventHandleProviderConfig


class InjectionTask(BaseModel):
    """An injection task to be executed."""

    target: Literal["agent", "context", "message", "tool", "instruction"] = Field(
        default="agent", description="The object to inject"
    )
    value: str = Field(default="", description="The value to inject")


class BaseEventHandleProvider(BaseProvider):
    """Abstract base class for event handle providers.

    This class provides event handling capabilities for providers that need to react
    to system events. Events are triggered by the Schwarm system at key points
    (message completion, tool execution, etc.), and providers can subscribe to handle
    these events.

    To handle events, providers should override the handle_* methods for the events
    they care about. The provider will be automatically subscribed to those events
    during initialization.
    """

    config: BaseEventHandleProviderConfig
    _event_handlers: dict[str, list[tuple[Callable, int]]] = {}  # {event_name: [(handler, priority)]}

    def __init__(self, agent: Agent, config: BaseEventHandleProviderConfig):
        """Initialize the provider with event handling capabilities."""
        super().__init__(agent, config)
        self._event_handlers = {}
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Sets up event handlers based on provider implementation.

        This method automatically subscribes to events based on which handler
        methods are implemented in the provider class. For example, if a provider
        overrides handle_message_completion, it will be subscribed to the
        on_message_completion event.
        """
        # Map of event names to their corresponding handler methods
        event_methods = {
            "on_start": self.handle_start,
            "on_handoff": self.handle_handoff,
            "on_message_completion": self.handle_message_completion,
            "on_tool_execution": self.handle_tool_execution,
            "on_post_message_completion": self.handle_post_message_completion,
            "on_post_tool_execution": self.handle_post_tool_execution,
            "on_instruct": self.handle_on_instruct,
            "on_post_instruct": self.handle_post_instruct,
        }

        # Subscribe to events based on which handlers are implemented
        for event_name, handler in event_methods.items():
            # Check if the handler is overridden in the child class
            if handler.__qualname__.split(".")[0] != "BaseEventHandleProvider":
                self.subscribe(event_name, handler)

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

    def handle_event(self, event_name: str, **kwargs: Any) -> Any:
        """Handle an event triggered by the system.

        This method is called by the Schwarm system when an event occurs. It executes
        all handlers subscribed to the event in priority order.

        Args:
            event_name: Name of the event to handle
            **kwargs: Event data passed by the system

        Returns:
            The result from the last handler, if any
        """
        result = None
        if event_name in self._event_handlers:
            for handler, _ in self._event_handlers[event_name]:
                try:
                    result = handler(**kwargs)
                except Exception as e:
                    logger.error(f"Error in event handler for {event_name}: {e}")
        return result

    # Base event handlers - providers should override these as needed
    def handle_start(self) -> InjectionTask | None:
        """Handle agent start event. (called once)."""
        pass

    def handle_on_instruct(self) -> InjectionTask | None:
        """Handle agent before instruction event."""
        pass

    def handle_post_instruct(self) -> InjectionTask | None:
        """Handle agent post instruction event."""
        pass

    def handle_handoff(self, next_agent: Agent) -> Agent | None:
        """Handle agent handoff event."""
        return next_agent

    def handle_message_completion(self) -> InjectionTask | None:
        """Handle message completion event."""
        pass

    def handle_tool_execution(self) -> InjectionTask | None:
        """Handle tool execution event."""
        pass

    def handle_post_message_completion(self) -> InjectionTask | None:
        """Handle post message completion event."""
        pass

    def handle_post_tool_execution(self) -> InjectionTask | None:
        """Handle post tool execution event."""
        pass
