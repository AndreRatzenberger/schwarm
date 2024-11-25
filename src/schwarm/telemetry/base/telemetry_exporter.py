"""Base class for custom OpenTelemetry exporters."""

from abc import ABC, abstractmethod

from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

from schwarm.configs.telemetry_config import TelemetryConfig


class TelemetryExporter(SpanExporter, ABC):
    """Base class for custom OpenTelemetry exporters."""

    config: TelemetryConfig

    def __init__(self, config: TelemetryConfig):
        """Base class for custom OpenTelemetry exporters."""
        self.config = config
        super().__init__()

    def _export(self, spans):
        """Forward spans to the Jaeger exporter."""
        try:
            result = self.export(spans)
            if result is None:
                return SpanExportResult.SUCCESS
            return result
        except Exception:
            return SpanExportResult.FAILURE
        finally:
            self.shutdown()

    @abstractmethod
    def export(self, spans) -> SpanExportResult | None:
        """Export spans to the configured backend.

        To be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the export method")

    @abstractmethod
    def shutdown(self):
        """Cleanup resources, if any. Optional for subclasses."""
        pass
