"""Exporter for sending OpenTelemetry spans to Jaeger."""

from opentelemetry.exporter.jaeger.thrift import JaegerExporter

from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter


class JaegerTelemetryExporter(TelemetryExporter):
    """Exporter for sending OpenTelemetry spans to Jaeger."""

    def __init__(self, host="localhost", port=6831):
        """Exporter for sending OpenTelemetry spans to Jaeger."""
        super().__init__()
        self.jaeger_exporter = JaegerExporter(
            agent_host_name=host,
            agent_port=port,
        )

    def export(self, spans):
        """Forward spans to the Jaeger exporter."""
        return self.jaeger_exporter.export(spans)

    def shutdown(self):
        """Shutdown the Jaeger exporter."""
        self.jaeger_exporter.shutdown()
