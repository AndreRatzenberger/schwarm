"""Base class for modern event handle providers."""

from collections.abc import Callable
from dataclasses import dataclass
from inspect import getmembers
from typing import Any, Generic, TypeVar

from loguru import logger

from schwarm.models.agent import Agent
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.models.base_event_handle_provider_config import BaseEventHandleProviderConfig
from schwarm.provider.base.models.injection import InjectionTarget, InjectionTask, InstructionInjection

T = TypeVar("T")


@dataclass
class Event(Generic[T]):
    """Type-safe event with payload."""

    type: str
    payload: T


class ModernEventHandleProvider(BaseProvider):
    """Modern base class for event handle providers.

    This class provides event handling capabilities through decorators rather than
    method overrides. Providers can use the @handles_event decorator to mark
    methods that should handle specific events.

    Example:
        class MyProvider(ModernEventHandleProvider):
            @handles_event(EventType.START)
            def initialize(self, event: Event[dict[str, Any]]) -> None:
                # Handle start event
                pass
    """

    config: BaseEventHandleProviderConfig
    _event_handlers: dict[str, list[tuple[Callable, int]]]

    def __init__(self, agent: Agent, config: BaseEventHandleProviderConfig):
        """Initialize the provider with event handling capabilities."""
        super().__init__(agent, config)
        self._event_handlers = {}
        self._setup_event_handlers()

    def _setup_event_handlers(self) -> None:
        """Sets up event handlers based on decorated methods.

        This method scans the provider class for methods decorated with
        @handles_event and registers them as handlers for their specified events.
        """
        for _, method in getmembers(self, predicate=lambda x: hasattr(x, "_handles_event")):
            event_type = getattr(method, "_event_type")
            priority = getattr(method, "_priority", 0)
            self.subscribe(event_type, method, priority)

    def subscribe(self, event_type: str, handler: Callable, priority: int = 0) -> None:
        """Subscribe a handler to an event type.

        Args:
            event_type: The type of event to handle
            handler: The handler function
            priority: Optional priority (higher executes first)
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []

        self._event_handlers[event_type].append((handler, priority))
        self._event_handlers[event_type].sort(key=lambda x: x[1], reverse=True)
        logger.debug(f"Subscribed to event {event_type} with priority {priority}")

    def handle_event(self, event: Event[Any]) -> InjectionTask | None:
        """Handle an event triggered by the system.

        Args:
            event: The event to handle

        Returns:
            Optional injection task to modify system behavior
        """
        result = None
        if event.type in self._event_handlers:
            for handler, _ in self._event_handlers[event.type]:
                try:
                    result = handler(event)
                except Exception as e:
                    logger.error(f"Error in event handler for {event.type}: {e}")
        return result

    def inject_instruction(self, content: str, position: str = "suffix") -> InjectionTask:
        """Helper method to create instruction injection."""
        return InjectionTask(
            target=InjectionTarget.INSTRUCTION,
            value=InstructionInjection(content=content, position=position),  # type: ignore
        )

    def initialize(self) -> None:
        """Initialize the provider."""
        super().initialize()
