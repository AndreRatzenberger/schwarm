"""TelemetryManager class for managing OpenTelemetry tracing configuration and provider-specific tracers."""

import sys
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.models.event import Event, SpanEvent
from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter
from schwarm.utils.handling import flatten_attributes, make_serializable


class TelemetryManager:
    """Manages OpenTelemetry tracing configuration and provider-specific tracers."""

    def __init__(
        self,
        telemetry_exporters: list[TelemetryExporter],
        enabled_providers: list[str] = [],
    ):
        """TelemetryManager class for managing OpenTelemetry tracing configuration and provider-specific tracers."""
        self.enabled_providers = set(enabled_providers or [])
        self.enabled_agents: dict[str, TelemetryConfig] = {}
        self.tracers: dict[str, trace.Tracer] = {}
        self.exporters: list[TelemetryExporter] = telemetry_exporters
        self.run_id: str = ""

        # Initialize OpenTelemetry
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)

        # Add exporters
        for exporter in telemetry_exporters:
            span_processor = SimpleSpanProcessor(exporter)
            tracer_provider.add_span_processor(span_processor)

        self.global_tracer = trace.get_tracer(__name__)
        sys.excepthook = self.log_exception_to_otel

    def log_exception_to_otel(self, exc_type, exc_value, exc_traceback):
        """Log unhandled exceptions to OpenTelemetry."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Allow normal handling of KeyboardInterrupt
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Use OpenTelemetry to record the exception
        with self.global_tracer.start_as_current_span("UnhandledException") as span:
            span.record_exception(exc_value)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(exc_value)))

    def add_agent(self, agent_name: str, config: TelemetryConfig):
        """Update the telemetry configuration."""
        self.enabled_agents[agent_name] = config

    def add_provide(self, provider_id: str):
        """Update the telemetry configuration."""
        self.enabled_providers.add(provider_id)

    def is_tracing_enabled(self, provider_id: str) -> bool:
        """Check if tracing is enabled for a specific provider."""
        return provider_id in self.enabled_providers

    def send_trace(self, global_context: SpanEvent):
        """Send a trace with global context."""
        if not self.global_tracer:
            raise RuntimeError("Tracer not set. Did you forget to register the provider?")
        context = flatten_attributes(make_serializable(global_context))

        name = f"{global_context.agent_name} - {global_context.event_type}"
        # if global_context.provider_id:
        #     name = f"{global_context.provider_id} - {global_context.agent_name} - {global_context.type}"

        with self.global_tracer.start_as_current_span(f"{name}") as span:
            span.set_attribute("event_type", str(global_context.event_type))
            span.set_attribute("agent_id", global_context.agent.name)
            span.set_attribute("run_id", self.run_id)
            for key, value in context.items():
                if isinstance(value, str | int | float | bool | bytes):
                    span.set_attribute(key, value)

    def send_provider_trace(self, global_context: Event):
        """Send a trace with global context."""
        if not self.global_tracer:
            raise RuntimeError("Tracer not set. Did you forget to register the provider?")
        context = flatten_attributes(make_serializable(global_context))

        name = f"{global_context.provider_id} - {global_context.agent_name} - {global_context.type}"

        with self.global_tracer.start_as_current_span(f"{name}") as span:
            span.set_attribute("event_type", str(global_context.type))
            span.set_attribute("agent_id", global_context.agent_name)
            span.set_attribute("run_id", self.run_id)
            for key, value in context.items():
                if isinstance(value, str | int | float | bool | bytes):
                    span.set_attribute(key, value)

    def send_any_object(self, object: Any, span):
        """Send a trace with global context."""
        if not self.global_tracer:
            raise RuntimeError("Tracer not set. Did you forget to register the provider?")
        flat_object = flatten_attributes(make_serializable(object))
        # span.set_attribute("context", context)
        for key, value in flat_object.items():
            span.set_attribute("run_id", self.run_id)
            if isinstance(value, str | int | float | bool | bytes):
                span.set_attribute(key, value)

    def get_tracer(self, provider_id: str) -> trace.Tracer:
        """Get a tracer for a specific provider.

        Args:
            provider_id (str): The provider ID for which to get a tracer.

        Returns:
            trace.Tracer: A tracer instance.
        """
        return self.global_tracer
