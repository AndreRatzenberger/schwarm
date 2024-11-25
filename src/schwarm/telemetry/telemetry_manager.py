"""TelemetryManager class for managing OpenTelemetry tracing configuration and provider-specific tracers."""

import json
from collections.abc import Sequence

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.models.event import Event
from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter
from schwarm.utils.handling import make_serializable


class TelemetryManager:
    """Manages OpenTelemetry tracing configuration and provider-specific tracers."""

    def __init__(self, telemetry_exporters: Sequence[TelemetryExporter], enabled_providers: list[str] = []):
        """TelemetryManager class for managing OpenTelemetry tracing configuration and provider-specific tracers."""
        self.enabled_providers = set(enabled_providers or [])
        self.enabled_agents: dict[str, TelemetryConfig] = {}
        self.tracers: dict[str, trace.Tracer] = {}
        self.exporters: Sequence[TelemetryExporter] = telemetry_exporters

        # Initialize OpenTelemetry
        tracer_provider = TracerProvider()
        trace.set_tracer_provider(tracer_provider)

        # Add exporters
        for exporter in telemetry_exporters:
            span_processor = BatchSpanProcessor(exporter)
            tracer_provider.add_span_processor(span_processor)

        self.global_tracer = trace.get_tracer(__name__)

    def add_agent(self, agent_name: str, config: TelemetryConfig):
        """Update the telemetry configuration."""
        self.enabled_agents[agent_name] = config

    def add_provide(self, provider_id: str):
        """Update the telemetry configuration."""
        self.enabled_providers.add(provider_id)

    def is_tracing_enabled(self, provider_id: str) -> bool:
        """Check if tracing is enabled for a specific provider."""
        return provider_id in self.enabled_providers

    def send_trace(self, global_context: Event):
        """Send a trace with global context."""
        if not self.global_tracer:
            raise RuntimeError("Tracer not set. Did you forget to register the provider?")
        context = json.dumps(make_serializable(global_context.context))

        name = f"{global_context.agent_name} - {global_context.type}"
        if global_context.provider_id:
            name = f"{global_context.provider_id} - {global_context.agent_name} - {global_context.type}"

        with self.global_tracer.start_as_current_span(f"{name}") as span:
            span.set_attribute("event_type", str(global_context.type))
            span.set_attribute("agent_id", global_context.agent_name)
            span.set_attribute("context", context)
            # for key, value in context.items():
            #     if isinstance(value, str | int | float | bool | bytes):
            #         span.set_attribute(key, value)

    def get_tracer(self, provider_id: str) -> trace.Tracer:
        """Get a tracer for a specific provider.

        Args:
            provider_id (str): The provider ID for which to get a tracer.

        Returns:
            trace.Tracer: A tracer instance.
        """
        return self.global_tracer
