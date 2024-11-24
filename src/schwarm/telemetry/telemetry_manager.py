"""TelemetryManager class for managing OpenTelemetry tracing configuration and provider-specific tracers."""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter


class TelemetryManager:
    """Manages OpenTelemetry tracing configuration and provider-specific tracers."""

    def __init__(self, telemetry_exporters: list[TelemetryExporter], enabled_providers: list[str]):
        """TelemetryManager class for managing OpenTelemetry tracing configuration and provider-specific tracers."""
        self.enabled_providers = set(enabled_providers or [])
        self.enabled_agents: dict[str, TelemetryConfig] = {}
        self.tracers: dict[str, trace.Tracer] = {}

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

    def send_trace(self, global_context: dict[str, str]):
        """Send a trace with global context."""
        tracer = self.get_tracer("global")
        if not self.get_tracer:
            raise RuntimeError("Tracer not set. Did you forget to register the provider?")

        with tracer.start_as_current_span(f"handle_event: {global_context}") as span:
            for key, value in global_context.items():
                span.set_attribute(key, value)

    def get_tracer(self, provider_id: str) -> trace.Tracer:
        """Get a tracer for a specific provider.

        Args:
            provider_id (str): The provider ID for which to get a tracer.

        Returns:
            trace.Tracer: A tracer instance.
        """
        if not self.is_tracing_enabled(provider_id):
            # Return a no-op tracer if tracing is disabled for this provider
            return trace.get_tracer("noop")

        # Return or create a tracer for this provider
        if provider_id not in self.tracers:
            self.tracers[provider_id] = trace.get_tracer(f"provider.{provider_id}")
        return self.tracers[provider_id]
