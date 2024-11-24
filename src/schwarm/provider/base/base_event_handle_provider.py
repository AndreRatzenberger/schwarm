"""Base class for event handle providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from opentelemetry.trace import Span

from schwarm.events.event_data import Event
from schwarm.provider.base.base_provider import BaseProvider, BaseProviderConfig
from schwarm.provider.provider_context import ProviderContext


class BaseEventHandleProviderConfig(BaseProviderConfig):
    """Configuration for event handle providers."""


@dataclass
class BaseEventHandleProvider(BaseProvider, ABC):
    """Base class for event handle providers."""

    event_log: list[Event] = field(default_factory=list)

    def _otm_init(self, event: Event) -> ProviderContext:
        if not self._tracer:
            raise RuntimeError("Tracer not set. Did you forget to register the provider?")

        with self._tracer.start_as_current_span(f"handle_event: {event.type}") as span:
            span.set_attribute("event.type", str(event.type))
            span.set_attribute("event.timestamp", str(event.datetime))
            span.set_attribute("event.payload", str(event.payload))  # Be cautious about PII!

            self.event_log.append(event)
            try:
                return self.handle_event(event, span)
            except Exception as e:
                span.record_exception(e)
                raise

    @abstractmethod
    def handle_event(self, event: Event, span: Span) -> ProviderContext:
        """Handle an event."""
        self.event_log.append(event)
