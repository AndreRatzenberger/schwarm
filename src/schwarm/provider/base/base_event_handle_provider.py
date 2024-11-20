from collections.abc import Callable
from typing import TYPE_CHECKING

from loguru import logger

from schwarm.events.event_data import Event
from schwarm.events.event_types import EventType
from schwarm.provider.base.base_provider import BaseProvider
from schwarm.provider.base.base_provider_config import BaseProviderConfig
from schwarm.provider.base.injection import InjectionTask

if TYPE_CHECKING:
    from schwarm.models.types import Agent


class BaseEventHandleProvider(BaseProvider):
    """Base class for providers that handle events."""

    def __init__(self, agent: Agent, config: BaseProviderConfig):
        self.config = config
        self.agent = agent
        self._event_handlers: dict[EventType, list[tuple[Callable, int]]] = {}
        self.context
        self._setup_handlers()

    def _setup_handlers(self) -> None:
        """Set up event handlers based on decorated methods."""
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, "event_type"):
                self.subscribe(attr.event_type, attr, getattr(attr, "priority", 0))

    def subscribe(self, event_type: EventType, handler: Callable, priority: int = 0) -> None:
        """Subscribe to an event with priority."""
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append((handler, priority))
        self._event_handlers[event_type].sort(key=lambda x: x[1], reverse=True)

    def handle_event(self, event: Event) -> InjectionTask | None:
        """Handle an event with proper typing."""
        if event.type in self._event_handlers:
            for handler, _ in self._event_handlers[event.type]:
                try:
                    result = handler(event)
                    if result is not None:
                        return result
                except Exception as e:
                    logger.error(f"Error in event handler for {event.type}: {e}")
        return None

    def inject_instruction(self, content: str, position: str = "suffix") -> InjectionTask:
        """Helper method to create instruction injection."""
        return InjectionTask(
            target="instruction",
            value=content,  # type: ignore
        )
