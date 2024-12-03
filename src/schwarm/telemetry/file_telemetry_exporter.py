"""Exporter to write spans to a file."""

from schwarm.configs.telemetry_config import TelemetryConfig
from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter


class FileTelemetryExporter(TelemetryExporter):
    """Exporter to write spans to a file."""

    def __init__(self, config: TelemetryConfig = TelemetryConfig(), file_path="schwarm_events.log"):
        """Initialize the exporter with a file path."""
        super().__init__(config)
        self.file_path = file_path

    def export(self, spans):
        """Write spans to a log file."""
        with open(self.file_path, "a") as f:
            for span in spans:
                f.write(f"{span.to_dict()}\n")
