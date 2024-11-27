"""Exporter to write spans to a file."""

from schwarm.telemetry.base.telemetry_exporter import TelemetryExporter


class FileTelemetryExporter(TelemetryExporter):
    """Exporter to write spans to a file."""

    def __init__(self, file_path="schwarm_events.log"):
        """Initialize the exporter with a file path."""
        super().__init__()
        self.file_path = file_path

    def export(self, spans):
        """Write spans to a log file."""
        with open(self.file_path, "a") as f:
            for span in spans:
                f.write(f"{span.to_dict()}\n")
